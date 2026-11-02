from io import BytesIO

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from docagent.config import get_settings
from docagent.db import Chunk, Document, Page, SessionLocal
from docagent.ingest.chunking import chunk_text
from docagent.ingest.pdf import extract_pages
from docagent.llm import embed_documents
from docagent.search.bm25 import bm25_index


def create_document(session: Session, filename: str, data: bytes) -> Document:
    doc = Document(filename=filename, num_pages=0, ocr_pages=0, status="processing", content=data)
    session.add(doc)
    session.commit()
    return doc


def process_document(document_id: int, data: bytes) -> None:
    s = get_settings()
    with SessionLocal() as session:
        doc = session.get(Document, document_id)
        if doc is None:
            return
        try:
            pages = extract_pages(BytesIO(data), ocr_language=s.ocr_language)
            pieces = [
                (p.number, piece)
                for p in pages
                for piece in chunk_text(p.text, s.chunk_size, s.chunk_overlap)
            ]
            vectors = embed_documents([text for _, text in pieces]) if pieces else []
            doc.pages = [Page(number=p.number, text=p.text, ocr=p.ocr) for p in pages]
            doc.chunks = [
                Chunk(page=page, text=text, embedding=vec)
                for (page, text), vec in zip(pieces, vectors, strict=True)
            ]
            doc.num_pages = len(pages)
            doc.ocr_pages = sum(p.ocr for p in pages)
            doc.status = "ready"
        except Exception as exc:
            session.rollback()
            doc = session.get_one(Document, document_id)
            doc.status = "failed"
            doc.error = str(exc) or type(exc).__name__
        try:
            session.commit()
        except SQLAlchemyError:
            session.rollback()
            return
        bm25_index.rebuild(session)


def ingest_pdf(session: Session, data: bytes, filename: str) -> Document:
    doc = create_document(session, filename, data)
    process_document(doc.id, data)
    session.refresh(doc)
    return doc
