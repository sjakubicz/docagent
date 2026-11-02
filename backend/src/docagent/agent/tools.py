from typing import Annotated

from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from sqlalchemy import select

from docagent.agent.options import options_from
from docagent.db import Document, Page, SessionLocal
from docagent.search.hybrid import SearchHit, search


@tool(
    response_format="content_and_artifact",
    description="Search the uploaded documents for passages relevant to the query.",
)
def search_documents(
    query: Annotated[str, "What to look for, phrased as keywords or a short question."],
    config: RunnableConfig,
    document_id: Annotated[int | None, "Optionally restrict the search to one document."] = None,
) -> tuple[str, list[SearchHit]]:
    options = options_from(config)
    with SessionLocal() as session:
        hits = search(
            session, query, k=options.top_k, mode=options.search_mode, document_id=document_id
        )

    if not hits:
        return "No matching passages found.", []

    return "\n\n".join(
        f"[{h.filename}, p. {h.page}] (document_id={h.document_id})\n{h.text}" for h in hits
    ), hits


@tool(description="List all uploaded documents with their ids and page counts.")
def list_documents() -> str:
    with SessionLocal() as session:
        docs = session.scalars(select(Document).order_by(Document.id)).all()
    if not docs:
        return "No documents have been uploaded."
    return "\n".join(f"document_id={d.id}: {d.filename} ({d.num_pages} pages)" for d in docs)


@tool(
    response_format="content_and_artifact",
    description="Read the full text of one page, e.g. to see context around a search result.",
)
def read_page(
    document_id: Annotated[int, "The document's id."],
    page: Annotated[int, "The 1-based page number."],
) -> tuple[str, list[SearchHit]]:
    with SessionLocal() as session:
        row = session.execute(
            select(Page.text, Document.filename)
            .join(Document)
            .where(Page.document_id == document_id, Page.number == page)
        ).first()
    if row is None:
        return f"Page {page} of document {document_id} does not exist.", []
    hit = SearchHit(
        chunk_id=-1,
        document_id=document_id,
        filename=row.filename,
        page=page,
        text=row.text,
        score=1.0,
    )
    return f"[{row.filename}, p. {page}]\n{row.text}", [hit]


TOOLS = [search_documents, list_documents, read_page]
