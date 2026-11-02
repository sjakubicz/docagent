from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import Session

from docagent.db import Chunk, Document
from docagent.llm import embed_query
from docagent.search.bm25 import bm25_index
from docagent.search.modes import Mode

RRF_K = 60


class SearchHit(BaseModel):
    model_config = ConfigDict(strict=True)

    chunk_id: int
    document_id: int
    filename: str
    page: int
    text: str
    score: float


def reciprocal_rank_fusion(rankings: list[list[int]], k: int = RRF_K) -> list[tuple[int, float]]:
    scores: dict[int, float] = {}
    for ranking in rankings:
        for rank, item in enumerate(ranking, start=1):
            scores[item] = scores.get(item, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda kv: kv[1], reverse=True)


def vector_search(session: Session, query: str, k: int) -> list[tuple[int, float]]:
    qvec = embed_query(query)
    distance = Chunk.embedding.cosine_distance(qvec)
    rows = session.execute(select(Chunk.id, distance).order_by(distance).limit(k)).all()
    return [(chunk_id, 1.0 - float(dist)) for chunk_id, dist in rows]


def search(
    session: Session,
    query: str,
    k: int = 5,
    mode: Mode = "hybrid",
    document_id: int | None = None,
) -> list[SearchHit]:
    candidates = max(k * 4, 20)
    if mode == "bm25":
        ranked = bm25_index.search(query, candidates)
    elif mode == "vector":
        ranked = vector_search(session, query, candidates)
    else:
        bm25_ids = [cid for cid, _ in bm25_index.search(query, candidates)]
        vector_ids = [cid for cid, _ in vector_search(session, query, candidates)]
        ranked = reciprocal_rank_fusion([bm25_ids, vector_ids])

    if not ranked:
        return []
    rows = session.execute(
        select(Chunk.id, Chunk.document_id, Document.filename, Chunk.page, Chunk.text)
        .join(Document)
        .where(Chunk.id.in_([cid for cid, _ in ranked]))
    ).all()
    by_id = {row.id: row for row in rows}

    hits: list[SearchHit] = []
    for chunk_id, score in ranked:
        row = by_id.get(chunk_id)
        if row is None or (document_id is not None and row.document_id != document_id):
            continue
        hits.append(
            SearchHit(
                chunk_id=chunk_id,
                document_id=row.document_id,
                filename=row.filename,
                page=row.page,
                text=row.text,
                score=score,
            )
        )
        if len(hits) == k:
            break
    return hits
