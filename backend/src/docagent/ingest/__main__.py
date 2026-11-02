import sys
from pathlib import Path

from docagent.db import SessionLocal, init_db
from docagent.ingest.pipeline import ingest_pdf

if __name__ == "__main__":
    init_db()
    with SessionLocal() as session:
        for arg in sys.argv[1:]:
            path = Path(arg)
            doc = ingest_pdf(session, path.read_bytes(), path.name)
            print(f"{path.name}: {doc.status}, {doc.num_pages} pages, {doc.ocr_pages} OCR")
