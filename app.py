"""Streamlit-app med raskere flyt og flerspråklig støtte.
   Oppdatering: tvungent svar kun i valgt språk.
"""
import streamlit as st
import tempfile
from concurrent.futures import ThreadPoolExecutor
from stqdm import stqdm

from utils.pdf_utils import pdf_to_text
from utils.llama_client import ask_llama

# Juster disse for din maskin
CHUNK_SIZE  = 6000
MAX_WORKERS = 4

# Språkvalg: bruker-label → (språkplattform, native prompt-frase)
# Språkvalg: bruker-label → (kode, native prompt-frase)
LANG_CHOICES = {
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

st.set_page_config(page_title="Forklar det offentlige", page_icon="📄")
st.title("📄 Forklar det offentlige for meg – lokal Llama 3 8B")

# Filopplasting + språkvalg
file = st.file_uploader("Last opp PDF", type=["pdf"])
lang_label = st.selectbox("Velg mål-språk", list(LANG_CHOICES.keys()), index=0)
lang_code, lang_phrase = LANG_CHOICES[lang_label]

if file:
    # 1) Middlertidig fil for pdfminer
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(file.read())
        pdf_path = tmp.name

    # 2) Ekstraher tekst (OCR kun om nødvendig)
    text = pdf_to_text(pdf_path)

    # 3) Chunking
    chunks = [text[i : i + CHUNK_SIZE] for i in range(0, len(text), CHUNK_SIZE)]
    st.info(f"Dokument delt i {len(chunks)} deler (~{CHUNK_SIZE} tegn hver).")

    # 4) Paralleliser LLM-kall
    def simplify_chunk(chunk: str) -> str:
        prompt = (
            f"Svar kun {lang_phrase}. Forklar teksten som til en 16-åring. "
            "Bruk korte setninger og punktlister:\n\n"
            + chunk
        )
        return ask_llama(prompt)

    simplified = []
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        for out in stqdm(pool.map(simplify_chunk, chunks), total=len(chunks)):
            simplified.append(out)

    # 5) Vis resultat
    result = "\n\n".join(simplified)
    st.success("Ferdig! Her er forklaringen:")
    st.text_area("Forklart versjon", value=result, height=400)
