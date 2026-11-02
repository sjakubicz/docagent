from functools import lru_cache

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from docagent.search.modes import Mode


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://docagent:docagent@localhost:5433/docagent"

    llm_base_url: str = "http://localhost:11434/v1"
    llm_api_key: SecretStr = SecretStr("ollama")
    llm_model: str = "qwen3:4b-instruct"
    llm_temperature: float = 0.1

    embed_base_url: str = "http://localhost:11434/v1"
    embed_api_key: SecretStr = SecretStr("ollama")
    embed_model: str = "nomic-embed-text"
    embed_dim: int = 768
    embed_query_prefix: str = "search_query: "
    embed_document_prefix: str = "search_document: "

    chunk_size: int = 800
    chunk_overlap: int = 150
    ocr_language: str = "eng"

    agent_max_steps: int = 6
    agent_search_mode: Mode = "hybrid"
    agent_top_k: int = 5


@lru_cache
def get_settings() -> Settings:
    return Settings()
