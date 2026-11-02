from io import BytesIO
from pathlib import Path

import pdfplumber
import pytesseract
from pydantic import BaseModel, ConfigDict

MIN_TEXT_CHARS = 20
OCR_RESOLUTION = 300


class PageText(BaseModel):
    model_config = ConfigDict(strict=True)

    number: int
    text: str
    ocr: bool


def extract_pages(file: str | Path | BytesIO, ocr_language: str = "eng") -> list[PageText]:
    pages: list[PageText] = []
    with pdfplumber.open(file) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = (page.extract_text() or "").strip()
            ocr = False
            if len(text) < MIN_TEXT_CHARS:
                image = page.to_image(resolution=OCR_RESOLUTION).original
                text = pytesseract.image_to_string(image, lang=ocr_language).strip()
                ocr = True
            pages.append(PageText(number=i, text=text, ocr=ocr))
    return pages
