from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Response, UploadFile
from langchain_core.messages import AIMessage, HumanMessage
from sqlalchemy import select
from sqlalchemy.orm import Session

from docagent.agent.graph import AgentResult, run_agent
from docagent.agent.options import ChatOptions
from docagent.api.schemas import ChatRequest, DocumentDetail, DocumentOut, SearchRequest
from docagent.db import Document, get_session
from docagent.ingest.pipeline import create_document, process_document
from docagent.search.bm25 import bm25_index
from docagent.search.hybrid import SearchHit, search

router = APIRouter(prefix="/api")
SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/documents", tags=["documents"])
def list_documents(session: SessionDep) -> list[DocumentOut]:
    docs = session.scalars(select(Document).order_by(Document.created_at.desc())).all()
    return [DocumentOut.model_validate(d) for d in docs]


@router.post("/documents", tags=["documents"], status_code=202)
def upload_document(
    file: UploadFile, session: SessionDep, background_tasks: BackgroundTasks
) -> DocumentOut:
    filename = file.filename or ""
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported.")
    data = file.file.read()
    doc = create_document(session, filename, data)
    background_tasks.add_task(process_document, doc.id, data)
    return DocumentOut.model_validate(doc)


def _get_document(session: Session, document_id: int) -> Document:
    doc = session.get(Document, document_id)
    if doc is None:
        raise HTTPException(404, "Document not found.")
    return doc


@router.get("/documents/{document_id}", tags=["documents"])
def get_document(document_id: int, session: SessionDep) -> DocumentDetail:
    return DocumentDetail.model_validate(_get_document(session, document_id))


@router.get(
    "/documents/{document_id}/file",
    tags=["documents"],
    response_class=Response,
    responses={200: {"content": {"application/pdf": {}}}},
)
def get_document_file(document_id: int, session: SessionDep) -> Response:
    doc = _get_document(session, document_id)
    if doc.content is None:
        raise HTTPException(404, "The original file is not stored for this document.")
    return Response(
        doc.content,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{doc.filename}"'},
    )


@router.delete("/documents/{document_id}", tags=["documents"], status_code=204)
def delete_document(document_id: int, session: SessionDep) -> None:
    session.delete(_get_document(session, document_id))
    session.commit()
    bm25_index.rebuild(session)


@router.post("/search", tags=["search"])
def search_chunks(req: SearchRequest, session: SessionDep) -> list[SearchHit]:
    return search(session, req.query, k=req.k, mode=req.mode)


@router.get("/chat/options", tags=["chat"])
def default_chat_options() -> ChatOptions:
    return ChatOptions.defaults()


@router.post("/chat", tags=["chat"])
def chat(req: ChatRequest) -> AgentResult:
    history = [
        HumanMessage(m.content) if m.role == "user" else AIMessage(m.content) for m in req.history
    ]
    return run_agent(req.message, history, req.options)
