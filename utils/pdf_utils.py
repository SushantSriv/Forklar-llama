"""PDF→tekst med intelligent fallback.
   1. Prøver ren tekst‑ekstraksjon (pdfminer).
   2. Hvis det mislykkes **og** ikke force_ocr, returneres teksten.
   3. Ellers OCR side for side med PyMuPDF + Tesseract.
"""
from pdfminer.high_level import extract_text
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
import io, logging

LOGGER = logging.getLogger(__name__)


def pdf_to_text(path: str, *, force_ocr: bool = False) -> str:
    """Returnerer ren tekst fra PDF. OCR kun ved behov."""
    try:
        text = extract_text(path)
    except Exception as exc:
        LOGGER.warning("pdfminer feilet – faller tilbake til OCR: %s", exc)
        text = ""

    if text and not force_ocr:
        return text

    # OCR‑fallback
    LOGGER.info("Starter OCR (kan ta tid)…")
    doc = fitz.open(path)
    pages = []
    for page in doc:
        pix = page.get_pixmap(dpi=300)
        img = Image.open(io.BytesIO(pix.tobytes()))
        pages.append(pytesseract.image_to_string(img, lang="nor"))
    return "\n".join(pages)
