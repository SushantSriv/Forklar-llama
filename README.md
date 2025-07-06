# Forklar – Explain Public Documents

**Forklar** is an open‑source Streamlit demo that turns dense Norwegian public documents into plain‑language explanations — in **your** language. It runs entirely locally using the **Llama 3 8B** model via Ollama, so no data ever leaves your machine.

---

## Why did I build this?

Norway’s public sector is transparent, but most official documents (housing sales prospectuses, condition reports, laws, application forms…) are only available in Norwegian.  For recent immigrants this is a real barrier:  misunderstandings can cost money, time, or even legal rights.  I wanted a *private* tool that

- **extracts the important points**,
- **translates / simplifies them** into the reader’s preferred language,
- **runs offline** so no sensitive PDFs are uploaded to third‑party servers.

---

## Key Features

|                     | **Explain tab** | **Compare tab**                     |
| ------------------- | --------------- | ----------------------------------- |
| Upload PDFs         | 1 file          | up to 4 files                       |
| Auto doc‑type guess | ✓ (overridable) | ✓ (overridable)                     |
| Languages           | 17 preset       | 17 preset                           |
| Live progress       | ✓               | ✓ (per column)                      |
| Special prompts     | —               | Sales prospectus & condition report |
| Side‑by‑side view   | —               | ✓                                   |
| Diff output         | —               | ✓ (for special types)               |
| Download PDF        | ✓               | — (coming)                          |

---

## Quick Start

```bash
# 1) Install Ollama & pull model
essudo install ollama
ollama pull llama3:8b

# 2) Clone & install app
git clone <repo>
cd forklar-llama
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# 3) Run
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Folder Structure

```
forklar-llama/
├─ app.py               # Streamlit UI
├─ requirements.txt     # Dependencies
├─ utils/
│  ├─ pdf_utils.py      # PDF → text (pdfminer + OCR fallback)
│  ├─ llama_client.py   # Minimal Ollama HTTP wrapper
│  └─ doc_classifier.py # Zero‑shot doc‑type guesser
└─ README.md            # You are here
```

---

## Roadmap

-

PRs and issues welcome!

---

## License

MIT © 2025 Your Name

