"""
Enkel HTTP-klient for Ollama.
"""

import os
import requests

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL_NAME  = os.getenv("MODEL_NAME",  "llama3:8b")

def ask_llama(
    prompt: str,
    temperature: float = 0.3,
    max_tokens: int = 400,
) -> str:
    """Returnerer ren tekstrespons fra /api/generate."""
    payload = {
        "model": MODEL_NAME,
        "prompt": prompt,
        "temperature": temperature,
        "num_predict": max_tokens,
        "stream": False,
    }

    try:
        # dropp timeout helt (→ ingen grense) ― eller sett f.eks. timeout=120
        r = requests.post(f"{OLLAMA_HOST}/api/generate", json=payload)
        r.raise_for_status()
        return r.json().get("response", "")
    except requests.RequestException as exc:
        return f"[Feil fra Ollama: {exc}]"
