from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.routing import APIRoute

from docagent.api.routes import router
from docagent.db import SessionLocal, init_db
from docagent.search.bm25 import bm25_index


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    with SessionLocal() as session:
        bm25_index.rebuild(session)
    yield


def _operation_id(route: APIRoute) -> str:
    return route.name


app = FastAPI(title="docagent", lifespan=lifespan, generate_unique_id_function=_operation_id)
app.include_router(router)
