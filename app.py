"""
📄 Forklar / Explain – Streamlit‑app
• Live‑oppdatering: viser **kun én aktiv del** av gangen (ny del erstatter
  forrige). Når genereringen er ferdig forsvinner visningen av deler.
• Lagrer forklaringen som PDF – filnavn «forklaring_<opplastet>.pdf».
"""

# ───────────── 1. Setup ─────────────
import streamlit as st
st.set_page_config(
    page_title="Explain My Document – Llama 3 8B",
    page_icon="📄",
    layout="wide",
)

import time, tempfile, textwrap
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from fpdf import FPDF

from utils.pdf_utils      import pdf_to_text
from utils.doc_classifier import classify_doc
from utils.llama_client   import ask_llama

# ───────────── 2. i18n ─────────────
T={
 "nb":{"title":"📄 Forklar dokumentet mitt – lokal Llama 3 8B","upload":"Last opp PDF‑fil","ui_lang":"Språk for dashbordet","explain_lang":"Språk for forklaringen","doctype":"Dokumenttype (kan overstyres)","button_generate":"🚀 Generer forklaring","chunks":"Dokumentet deles i **{n}** deler.","done":"Ferdig! Generering tok **{sec:.1f} sekunder**.","summary":"📝 Kort sammendrag","explanation":"Forklaring","raw_text":"🔍 Original tekst (før forenkling)","model_settings":"⚙️ Modell‑innstillinger","temperature":"Temperature","max_tokens":"Max tokens","temp_help":"Lav verdi → mer deterministisk (ofte raskere).","tokens_help":"Øvre grense for genererte token per chunk.","doc_error":"Fant ingen tekst i PDF‑en.","processing":"Genererer, vennligst vent…","download_pdf":"Last ned som PDF"},
 "en":{"title":"📄 Explain my document – local Llama 3 8B","upload":"Upload PDF file","ui_lang":"Dashboard language","explain_lang":"Language for explanation","doctype":"Document type (you can override)","button_generate":"🚀 Generate explanation","chunks":"Document is split into **{n}** parts.","done":"Done! Generation took **{sec:.1f} seconds**.","summary":"📝 Short summary","explanation":"Explanation","raw_text":"🔍 Raw text (before simplification)","model_settings":"⚙️ Model settings","temperature":"Temperature","max_tokens":"Max tokens","temp_help":"Low = deterministic & faster.","tokens_help":"Upper limit for generated tokens per chunk.","doc_error":"No text found in the PDF.","processing":"Processing, please wait…","download_pdf":"Download as PDF"},
}


DOC_LABEL={
 "nb":{"lovtekst":"Lovtekst","veiledning":"Veiledning","rapport":"Rapport","søknad":"Søknad","skjema":"Skjema","notat":"Notat","budsjett":"Budsjett","default":"Annet"},
 "en":{"lovtekst":"Legal text","veiledning":"Guide","rapport":"Report","søknad":"Application","skjema":"Form","notat":"Memo","budsjett":"Budget","default":"Other"},
}

def tr(k:str)->str:
    return T[st.session_state.get("ui_lang","nb")][k]

# ───────────── 3. Konfig ─────────────
if "ui_lang" not in st.session_state:
    st.session_state["ui_lang"]="nb"

CHUNK_SIZE=6000
MAX_WORKERS=4
LANG_CHOICES = {  # label → (kode, «på …»)
    "Norsk":    ("norsk",    "på norsk"),
    "English":  ("english",  "in English"),
    "Polsk":    ("polish",   "po polsku"),
    "Arabisk":  ("arabic",   "بالعربية"),
    "Somali":   ("somali",   "af Soomaali"),
    "Deutsch":  ("german",   "auf Deutsch"),
    "Français": ("french",   "en français"),
    "Español":  ("spanish",  "en español"),
    "Italiano": ("italian",  "in italiano"),
    "Hindi":    ("hindi",    "हिंदी में"),
    "Bengali":  ("bengali",  "বাংলায়"),
    "Punjabi":  ("punjabi",  "ਪੰਜਾਬੀ ਵਿੱਚ"),
    "Tamil":    ("tamil",    "தமிழில்"),
    "Telugu":   ("telugu",   "తెలుగులో"),
    "Marathi":  ("marathi",  "मराठीत"),
    "Gujarati": ("gujarati","ગુજરાતીમાં"),
    "Urdu":     ("urdu",     "اردو میں")
}


PROMPT_TEMPLATES={
 "lovtekst":"Svar kun {lang_phrase}. Du er en juridisk formidler. Forklar teksten for en 16-åring i maks 6 punkt:\n\n{chunk}",
 "veiledning":"Svar kun {lang_phrase}. Du er en pedagog. Oppsummer trinnvis i maks 6 punkt:\n\n{chunk}",
 "rapport":"Svar kun {lang_phrase}. Du er en journalist. Presenter hovedpoengene i maks 8 punkt:\n\n{chunk}",
 "søknad":"Svar kun {lang_phrase}. Du er en rådgiver. Forklar hvordan man fyller ut søknaden i maks 6 punkt:\n\n{chunk}",
 "skjema":"Svar kun {lang_phrase}. Du er en veileder. Gå felt for felt og beskriv hva som skal fylles inn:\n\n{chunk}",
 "notat":"Svar kun {lang_phrase}. Du er en sekretær. Oppsummer hovedpoengene i maks 5 punkt:\n\n{chunk}",
 "budsjett":"Svar kun {lang_phrase}. Du er en økonom. Fremhev nøkkeltall i maks 8 punkt:\n\n{chunk}",
 "default":"Svar kun {lang_phrase}. Forklar teksten som til en 16-åring. Bruk korte setninger og punktlister:\n\n{chunk}",
}

# ───────────── 4. UI ─────────────
st.sidebar.selectbox("🌐 "+tr("ui_lang"),["nb","en"],format_func=lambda c:{"nb":"Norsk","en":"English"}[c],key="ui_lang")

st.title(tr("title"))
with st.sidebar:
    st.header(tr("model_settings"))
    temperature=st.slider(tr("temperature"),0.0,1.0,0.3,0.05,help=tr("temp_help"))
    max_tokens=st.number_input(tr("max_tokens"),64,4096,400,32,help=tr("tokens_help"))

file=st.file_uploader(tr("upload"),type=["pdf"])
explain_label=st.selectbox(tr("explain_lang"),list(LANG_CHOICES.keys()))
_,explain_phrase=LANG_CHOICES[explain_label]

# ───────────── 5. Hovedlogikk ─────────────
if file:
    # 5-A  Vis fremdrift mens vi skriver til disk og trekker ut tekst
    prep_bar = st.progress(0.0)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file.read())
        pdf_path = tmp.name
    prep_bar.progress(0.5)                     # halvveis (PDF lagret)

    text = pdf_to_text(pdf_path)
    prep_bar.progress(1.0)                     # ferdig
    prep_bar.empty()                           # skjul baren

    if not text.strip():
        st.error(tr("doc_error"))
        st.stop()

    codes = [
        "lovtekst", "veiledning", "rapport", "søknad",
        "skjema", "notat", "budsjett", "default",
    ]
    auto_type = classify_doc(text)
    doc_type = st.selectbox(
        tr("doctype"),
        codes,
        index=codes.index(auto_type) if auto_type in codes else codes.index("default"),
        format_func=lambda c: DOC_LABEL[st.session_state["ui_lang"]][c],
    )

    if st.button(tr("button_generate"), type="primary"):
        chunks = [text[i : i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
        st.markdown(tr("chunks").format(n=len(chunks)))

        live_placeholder = st.empty()      # overskrives for hver ferdige del
        progress = st.progress(0.0)
        results = [None] * len(chunks)

        def simplify_pair(pair):
            idx, chunk = pair
            prompt = PROMPT_TEMPLATES.get(
                doc_type, PROMPT_TEMPLATES["default"]
            ).format(chunk=chunk, lang_phrase=explain_phrase)
            return idx, ask_llama(prompt, temperature, max_tokens)

        t0 = time.perf_counter()
        with st.spinner(tr("processing")):
            with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
                futures = {
                    pool.submit(simplify_pair, p): p[0] for p in enumerate(chunks)
                }
                completed = 0
                for fut in as_completed(futures):
                    idx, txt = fut.result()
                    results[idx] = txt
                    live_placeholder.markdown(
                        f"**{DOC_LABEL[st.session_state['ui_lang']][doc_type]} – "
                        f"{idx+1}/{len(chunks)}**\n\n{txt}"
                    )
                    completed += 1
                    progress.progress(completed / len(chunks))

        elapsed = time.perf_counter() - t0
        progress.empty()
        live_placeholder.empty()            # skjul siste del

        full_text = "\n\n".join(results)
        st.success(tr("done").format(sec=elapsed))
        with st.expander(tr("summary"), expanded=True):
            st.markdown(textwrap.shorten(full_text, width=500, placeholder="…"))
        st.text_area(tr("explanation"), full_text, height=400)

        # 5-B  PDF-generering & nedlasting
        def create_pdf(txt: str) -> bytes:
            pdf = FPDF()
            pdf.set_auto_page_break(True, 15)
            pdf.add_page()
            pdf.set_font("Helvetica", size=12)
            for line in txt.splitlines():
                clean = line.encode("latin-1", "replace").decode("latin-1")
                pdf.multi_cell(0, 8, clean)
            return pdf.output(dest="S").encode("latin-1", "replace")

        stem = Path(file.name).stem or "dokument"
        st.download_button(
            label=tr("download_pdf"),
            data=create_pdf(full_text),
            file_name=f"forklaring_{stem}.pdf",
            mime="application/pdf",
        )
