"""Liten wrapper rundt Ollama REST‑API."""
import os, requests, json
from dotenv import load_dotenv

load_dotenv()
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
MODEL = os.getenv("MODEL_NAME", "llama3:8b")


def ask_llama(prompt: str, *, system: str = "", temp: float = 0.2, max_tokens: int = 1024) -> str:
    body = {
        "model": MODEL,
        "prompt": prompt,
        "system": system,
        "stream": False,
        "temperature": temp,
        "top_p": 0.95,
        "max_tokens": max_tokens,
    }
    r = requests.post(f"{OLLAMA_HOST}/api/generate", json=body, timeout=600)
    r.raise_for_status()
    return json.loads(r.text)["response"]
