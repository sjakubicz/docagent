import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from langchain_core.language_models import LanguageModelInput
from langchain_core.messages import (
    AIMessage,
    AnyMessage,
    BaseMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
from langchain_core.runnables import Runnable, RunnableConfig
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel, ConfigDict, Field

from docagent.agent.options import ChatOptions, options_from
from docagent.agent.tools import TOOLS, search_documents
from docagent.llm import chat_model, strip_thinking
from docagent.search.hybrid import SearchHit

SYSTEM_PROMPT = (Path(__file__).parent / "system.md").read_text(encoding="utf-8").strip()

TOOLS_BY_NAME = {t.name: t for t in TOOLS}


def _current_turn(messages: list[AnyMessage]) -> list[AnyMessage]:
    for i in range(len(messages) - 1, -1, -1):
        if isinstance(messages[i], HumanMessage):
            return messages[i:]
    return messages


INITIAL_SEARCH_ID = "initial_search"


def _retrieve_node(state: MessagesState, config: RunnableConfig) -> dict[str, list[AnyMessage]]:
    question = str(_current_turn(state["messages"])[0].content)
    call: dict[str, Any] = {
        "name": "search_documents",
        "args": {"query": question},
        "id": INITIAL_SEARCH_ID,
        "type": "tool_call",
    }
    result = search_documents.invoke(call, config)
    return {"messages": [AIMessage("", tool_calls=[call]), result]}


def _agent_node(state: MessagesState, config: RunnableConfig) -> dict[str, list[BaseMessage]]:
    steps = sum(isinstance(m, AIMessage) for m in _current_turn(state["messages"]))
    llm: Runnable[LanguageModelInput, BaseMessage] = chat_model()
    if steps < options_from(config).max_steps:
        llm = chat_model().bind_tools(TOOLS)
    response = llm.invoke([SystemMessage(SYSTEM_PROMPT), *state["messages"]])
    return {"messages": [response]}


def _tools_node(state: MessagesState, config: RunnableConfig) -> dict[str, list[ToolMessage]]:
    last = state["messages"][-1]
    assert isinstance(last, AIMessage)
    results: list[ToolMessage] = []
    for call in last.tool_calls:
        tool = TOOLS_BY_NAME.get(call["name"])
        if tool is None:
            message = f"Unknown tool {call['name']!r}."
            results.append(ToolMessage(message, tool_call_id=call["id"], status="error"))
            continue
        try:
            results.append(tool.invoke(call, config))
        except Exception as exc:
            message = f"Tool error: {exc}"
            results.append(ToolMessage(message, tool_call_id=call["id"], status="error"))
    return {"messages": results}


def _route(state: MessagesState) -> str:
    last = state["messages"][-1]
    return "tools" if isinstance(last, AIMessage) and last.tool_calls else END


def build_graph() -> CompiledStateGraph[MessagesState]:
    graph = StateGraph(MessagesState)
    graph.add_node("retrieve", _retrieve_node)
    graph.add_node("agent", _agent_node)
    graph.add_node("tools", _tools_node)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "agent")
    graph.add_conditional_edges("agent", _route, ["tools", END])
    graph.add_edge("tools", "agent")
    return graph.compile()


agent_graph = build_graph()


class ToolStep(BaseModel):
    model_config = ConfigDict(strict=True, json_schema_serialization_defaults_required=True)

    name: str
    args: dict[str, Any]
    automatic: bool = False
    output: str = ""
    hits: list[SearchHit] = Field(default_factory=list)
    error: bool = False


class AgentResult(BaseModel):
    model_config = ConfigDict(strict=True, json_schema_serialization_defaults_required=True)

    answer: str
    options: ChatOptions
    steps: list[ToolStep] = Field(default_factory=list)
    duration_ms: int = 0


def _collect_steps(messages: Sequence[BaseMessage]) -> list[ToolStep]:
    results = {m.tool_call_id: m for m in messages if isinstance(m, ToolMessage)}
    steps: list[ToolStep] = []
    for msg in messages:
        if not isinstance(msg, AIMessage):
            continue
        for call in msg.tool_calls:
            result = results.get(call["id"] or "")
            steps.append(
                ToolStep(
                    name=call["name"],
                    args=call["args"],
                    automatic=call["id"] == INITIAL_SEARCH_ID,
                    output=str(result.content) if result else "",
                    hits=list(result.artifact or []) if result else [],
                    error=result is not None and result.status == "error",
                )
            )
    return steps


def run_agent(
    question: str,
    history: Sequence[AnyMessage] | None = None,
    options: ChatOptions | None = None,
) -> AgentResult:
    options = options or ChatOptions.defaults()
    messages: list[AnyMessage] = [*(history or []), HumanMessage(question)]
    started = time.perf_counter()
    final = agent_graph.invoke(
        {"messages": messages},
        {"recursion_limit": 50, "configurable": {"options": options}},
    )
    new_messages = final["messages"][len(messages) :]
    return AgentResult(
        answer=strip_thinking(str(new_messages[-1].content)),
        options=options,
        steps=_collect_steps(new_messages),
        duration_ms=round((time.perf_counter() - started) * 1000),
    )
