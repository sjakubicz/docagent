import pytest
from pydantic import ValidationError

from docagent.agent.graph import AgentResult, ToolStep
from docagent.agent.options import ChatOptions
from docagent.ingest.pdf import PageText
from docagent.search.hybrid import SearchHit

HIT = {"chunk_id": 1, "document_id": 1, "filename": "a.pdf", "page": 2, "text": "x", "score": 0.5}


def test_search_hit_rejects_wrong_types():
    with pytest.raises(ValidationError):
        SearchHit.model_validate({**HIT, "page": "2"})
    with pytest.raises(ValidationError):
        SearchHit.model_validate({k: v for k, v in HIT.items() if k != "score"})


def test_other_models_reject_wrong_types():
    with pytest.raises(ValidationError):
        PageText.model_validate({"number": 1, "text": "x", "ocr": "yes"})
    with pytest.raises(ValidationError):
        ToolStep.model_validate({"name": "read_page", "args": "page=2"})
    with pytest.raises(ValidationError):
        AgentResult.model_validate({"answer": None})


def test_agent_result_defaults_are_independent():
    options = ChatOptions.defaults()
    a, b = AgentResult(answer="a", options=options), AgentResult(answer="b", options=options)
    a.steps.append(ToolStep(name="read_page", args={}, hits=[SearchHit.model_validate(HIT)]))
    assert b.steps == []
