from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from docagent.agent.options import ChatOptions
from docagent.search.modes import Mode


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    filename: str
    num_pages: int
    ocr_pages: int
    status: Literal["processing", "ready", "failed"]
    error: str | None
    created_at: datetime
    has_file: bool


class PageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    number: int
    text: str
    ocr: bool


class DocumentDetail(DocumentOut):
    pages: list[PageOut]


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    k: int = Field(default=5, ge=1, le=50)
    mode: Mode = "hybrid"


class ChatMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=1)
    history: list[ChatMessage] = []
    options: ChatOptions | None = None
