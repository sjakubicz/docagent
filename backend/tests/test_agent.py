from langchain_core.messages import AIMessage

from docagent.agent import graph
from docagent.agent.options import ChatOptions
from docagent.ingest.pipeline import ingest_pdf


class FakeChatModel:
    def __init__(self, responses: list[AIMessage]) -> None:
        self.responses = responses
        self.calls: list[bool] = []

    def bind_tools(self, tools: list) -> BoundFakeChatModel:
        return BoundFakeChatModel(self)

    def invoke(self, messages: list, with_tools: bool = False) -> AIMessage:
        self.calls.append(with_tools)
        return self.responses.pop(0)


class BoundFakeChatModel:
    def __init__(self, model: FakeChatModel) -> None:
        self.model = model

    def invoke(self, messages: list) -> AIMessage:
        return self.model.invoke(messages, with_tools=True)


def tool_call(name: str, args: dict, call_id: str) -> AIMessage:
    return AIMessage("", tool_calls=[{"name": name, "args": args, "id": call_id}])


def test_agent_searches_first_then_uses_tools(db, sample_pdf, monkeypatch):
    doc = ingest_pdf(db, sample_pdf.read_bytes(), sample_pdf.name)
    fake = FakeChatModel(
        [
            tool_call("read_page", {"document_id": doc.id, "page": 2}, "c1"),
            AIMessage("Limit sodium to 2 g per day [hypertension_care_plan.pdf, p. 2]."),
        ]
    )
    monkeypatch.setattr(graph, "chat_model", lambda: fake)

    result = graph.run_agent("How much salt is allowed?")

    first, second = result.steps
    assert (first.name, first.automatic, first.args) == (
        "search_documents",
        True,
        {"query": "How much salt is allowed?"},
    )
    assert first.hits and all(h.filename == sample_pdf.name for h in first.hits)
    assert (second.name, second.automatic, second.error) == ("read_page", False, False)
    assert [(h.filename, h.page) for h in second.hits] == [(sample_pdf.name, 2)]
    assert "Lifestyle and Monitoring" in second.output
    assert result.answer.startswith("Limit sodium")
    assert result.options == ChatOptions.defaults()
    assert fake.calls == [True, True]


def test_options_control_search(db, sample_pdf, monkeypatch):
    ingest_pdf(db, sample_pdf.read_bytes(), sample_pdf.name)
    monkeypatch.setattr(graph, "chat_model", lambda: FakeChatModel([AIMessage("ok")]))
    options = ChatOptions(search_mode="bm25", top_k=1, max_steps=3)

    result = graph.run_agent("lisinopril dry cough", options=options)

    assert result.options == options
    assert len(result.steps[0].hits) == 1


def test_agent_answers_without_tools_when_budget_is_spent(db, monkeypatch):
    fake = FakeChatModel(
        [
            tool_call("list_documents", {}, "c1"),
            AIMessage("No documents have been uploaded."),
        ]
    )
    monkeypatch.setattr(graph, "chat_model", lambda: fake)
    options = ChatOptions(search_mode="hybrid", top_k=5, max_steps=2)

    result = graph.run_agent("What documents do I have?", options=options)

    assert fake.calls == [True, False]
    assert result.steps[1].output == "No documents have been uploaded."
    assert result.answer == "No documents have been uploaded."


def test_unknown_tool_is_reported_back_to_model(db, monkeypatch):
    fake = FakeChatModel([tool_call("delete_everything", {}, "c1"), AIMessage("I cannot do that.")])
    monkeypatch.setattr(graph, "chat_model", lambda: fake)

    result = graph.run_agent("Delete everything")

    assert result.answer == "I cannot do that."
    assert [(s.name, s.error) for s in result.steps] == [
        ("search_documents", False),
        ("delete_everything", True),
    ]


def test_strip_thinking():
    assert graph.strip_thinking("<think>hmm</think>\nAnswer") == "Answer"


def test_chat_options_endpoint_returns_defaults(client):
    assert client.get("/api/chat/options").json() == ChatOptions.defaults().model_dump()


def test_chat_endpoint_passes_history_and_options(client, monkeypatch):
    seen: list[tuple] = []

    def fake_run_agent(question, history, options):
        seen.append((history, options))
        return graph.AgentResult(answer=f"echo: {question}", options=options)

    monkeypatch.setattr("docagent.api.routes.run_agent", fake_run_agent)
    options = {"search_mode": "vector", "top_k": 3, "max_steps": 4}
    response = client.post(
        "/api/chat",
        json={
            "message": "and now?",
            "history": [
                {"role": "user", "content": "hi"},
                {"role": "assistant", "content": "hello"},
            ],
            "options": options,
        },
    )
    body = response.json()
    assert (body["answer"], body["options"], body["steps"]) == ("echo: and now?", options, [])
    history, received = seen[0]
    assert [m.type for m in history] == ["human", "ai"]
    assert received == ChatOptions(**options)


def test_chat_rejects_out_of_range_options(client):
    options = {"search_mode": "hybrid", "top_k": 99, "max_steps": 4}
    response = client.post("/api/chat", json={"message": "hi", "options": options})
    assert response.status_code == 422
