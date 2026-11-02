from typing import Self

from langchain_core.runnables import RunnableConfig
from pydantic import BaseModel, Field

from docagent.config import get_settings
from docagent.search.modes import Mode

MAX_TOP_K = 20
MAX_STEPS = 10


class ChatOptions(BaseModel):
    search_mode: Mode
    top_k: int = Field(ge=1, le=MAX_TOP_K)
    max_steps: int = Field(ge=1, le=MAX_STEPS)

    @classmethod
    def defaults(cls) -> Self:
        s = get_settings()
        return cls(
            search_mode=s.agent_search_mode, top_k=s.agent_top_k, max_steps=s.agent_max_steps
        )


def options_from(config: RunnableConfig) -> ChatOptions:
    options = config.get("configurable", {}).get("options")
    return options if isinstance(options, ChatOptions) else ChatOptions.defaults()
