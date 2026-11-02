import threading

import bm25s
from sqlalchemy import select
from sqlalchemy.orm import Session

from docagent.db import Chunk


class BM25Index:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._retriever: bm25s.BM25 | None = None
        self._chunk_ids: list[int] = []

    def rebuild(self, session: Session) -> None:
        rows = session.execute(select(Chunk.id, Chunk.text).order_by(Chunk.id)).all()
        retriever = None
        if rows:
            retriever = bm25s.BM25()
            retriever.index(
                bm25s.tokenize([text for _, text in rows], stopwords="en", show_progress=False),
                show_progress=False,
            )
        with self._lock:
            self._retriever = retriever
            self._chunk_ids = [chunk_id for chunk_id, _ in rows]

    def search(self, query: str, k: int) -> list[tuple[int, float]]:
        with self._lock:
            retriever, chunk_ids = self._retriever, self._chunk_ids
        if retriever is None:
            return []
        tokens = bm25s.tokenize([query], stopwords="en", return_ids=False, show_progress=False)
        if not any(tokens):
            return []
        docs, scores = retriever.retrieve(tokens, k=min(k, len(chunk_ids)), show_progress=False)
        return [
            (chunk_ids[int(i)], float(sc))
            for i, sc in zip(docs[0], scores[0], strict=True)
            if sc > 0
        ]


bm25_index = BM25Index()
