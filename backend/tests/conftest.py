import hashlib
import os
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest
from psycopg import sql
from sqlalchemy import make_url

TEST_DATABASE_URL = os.environ.setdefault(
    "TEST_DATABASE_URL", "postgresql+psycopg://docagent:docagent@localhost:5433/docagent_test"
)
os.environ["DATABASE_URL"] = TEST_DATABASE_URL

from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.orm import Session

from docagent import llm
from docagent.config import get_settings
from docagent.db import SessionLocal, engine, init_db
from docagent.search.bm25 import bm25_index

SAMPLES = Path(__file__).parents[2] / "data" / "samples"


def fake_embed(texts: list[str]) -> list[list[float]]:
    dim = get_settings().embed_dim
    vectors = []
    for t in texts:
        vec = [0.0] * dim
        for word in t.lower().split():
            vec[int(hashlib.md5(word.encode()).hexdigest(), 16) % dim] += 1.0
        norm = sum(v * v for v in vec) ** 0.5 or 1.0
        vectors.append([v / norm for v in vec])
    return vectors


@pytest.fixture(autouse=True)
def no_network_embeddings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(llm, "_embed", fake_embed)


def _ensure_database(url: str) -> None:
    sa_url = make_url(url)
    name = sa_url.database
    if not name:
        raise ValueError(f"TEST_DATABASE_URL has no database name: {url}")
    admin = sa_url.set(drivername="postgresql", database="postgres").render_as_string(
        hide_password=False
    )
    with psycopg.connect(admin, autocommit=True, connect_timeout=3) as conn:
        exists = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (name,)).fetchone()
        if not exists:
            conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))


@pytest.fixture(scope="session")
def database() -> None:
    try:
        _ensure_database(TEST_DATABASE_URL)
    except psycopg.OperationalError as exc:
        pytest.skip(f"Test database unavailable: {exc}")
    init_db()


@pytest.fixture
def db(database: None) -> Iterator[Session]:
    with SessionLocal() as session:
        yield session
    with engine.begin() as conn:
        conn.execute(text("TRUNCATE documents RESTART IDENTITY CASCADE"))
    with SessionLocal() as session:
        bm25_index.rebuild(session)


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    from docagent.main import app

    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def sample_pdf() -> Path:
    return SAMPLES / "hypertension_care_plan.pdf"


@pytest.fixture
def scanned_pdf() -> Path:
    return SAMPLES / "knee_surgery_instructions_scan.pdf"
