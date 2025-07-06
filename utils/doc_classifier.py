# utils/doc_classifier.py

from utils.llama_client import ask_llama

# Maks antall tegn vi sender til klassifisering (unngå veldig lange prompts)
MAX_CLASSIFY_CHARS = 2000

def classify_doc(text: str) -> str:
    """
    Klassifiserer dokumentet som én av:
      - 'lovtekst'
      - 'veiledning'
      - 'rapport'
      - 'default'
    ved å sende en kort prompt til Llama via ask_llama.
    """
    snippet = text[:MAX_CLASSIFY_CHARS].strip().replace("\n", " ")
    prompt = (
        "Klassifiser følgende tekst som én av: lovtekst, veiledning, rapport eller default.\n"
        "Svar kun med én av disse etikettene (uten andre ord):\n\n"
        f"{snippet}"
    )
    label = ask_llama(prompt).strip().lower()

    # Rydd opp i label og sjekk gyldighet
    if label in {"lovtekst", "veiledning", "rapport"}:
        return label
    return "default"
