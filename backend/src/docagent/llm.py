import re
from functools import lru_cache

from langchain_openai import ChatOpenAI
from openai import OpenAI

from docagent.config import get_settings

_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)


@lru_cache
def chat_model() -> ChatOpenAI:
    s = get_settings()
    return ChatOpenAI(
        base_url=s.llm_base_url,
        api_key=s.llm_api_key,
        model=s.llm_model,
        temperature=s.llm_temperature,
    )


@lru_cache
def _embed_client() -> OpenAI:
    s = get_settings()
    return OpenAI(base_url=s.embed_base_url, api_key=s.embed_api_key.get_secret_value())


def _embed(texts: list[str]) -> list[list[float]]:
    s = get_settings()
    vectors: list[list[float]] = []
    for i in range(0, len(texts), 64):
        resp = _embed_client().embeddings.create(model=s.embed_model, input=texts[i : i + 64])
        vectors.extend(item.embedding for item in resp.data)
    return vectors


def embed_documents(texts: list[str]) -> list[list[float]]:
    prefix = get_settings().embed_document_prefix
    return _embed([prefix + t for t in texts])


def embed_query(text: str) -> list[float]:
    return _embed([get_settings().embed_query_prefix + text])[0]


def strip_thinking(text: str) -> str:
    return _THINK_RE.sub("", text).strip()
