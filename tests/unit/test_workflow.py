import pytest
from unittest.mock import AsyncMock, patch

from backend.app.graph.workflow import CoFounderWorkflow
from backend.app.models.state import RunState
from backend.app.models.schemas import (
    MarketAnalystOutput,
    MarketMetric,
    CompetitorItem,
    ProductManagerOutput,
    Persona,
    FeatureItem,
    TechArchitectOutput,
    StackChoice,
    ArchitectureComponent,
    MonthlyCostEstimate,
    PitchWriterOutput,
    PitchSlide,
    CEOCriticReview,
)


@pytest.fixture
def workflow():
    return CoFounderWorkflow(provider="ollama", model_default="qwen3:4b", model_critic="qwen3:4b")


def test_workflow_compilation(workflow):
    assert workflow.graph is not None


@pytest.mark.asyncio
async def test_intake_node(workflow):
    initial_state: RunState = {
        "run_id": "test-run-123",
        "idea": "AI tutor for Class 10 students in India",
        "market": None,
        "prd": None,
        "architecture": None,
        "pitch": None,
        "scores": {},
        "debate_log": [],
        "retries": {},
        "token_usage": {},
        "status": "queued",
        "options": {"debate_rounds": 2, "score_threshold": 7.0},
        "current_agent": None,
        "errors": [],
        "debate_round": 0,
        "user_id": None
    }
    updates = await workflow.intake_node(initial_state)
    assert updates["status"] == "running"
    assert "scores" in updates
    assert "retries" in updates


def test_routing_market_pass_advances(workflow):
    state: RunState = {
        "run_id": "r1",
        "idea": "Idea",
        "market": {},
        "prd": None,
        "architecture": None,
        "pitch": None,
        "scores": {"market": [8.0]},
        "debate_log": [],
        "retries": {"market": 0},
        "token_usage": {},
        "status": "running",
        "options": {"score_threshold": 7.0},
        "current_agent": "market_analyst",
        "errors": [],
        "debate_round": 0,
        "user_id": None,
        "_last_review": {"score": 8.0, "pass": True}
    }
    next_node = workflow.should_retry_market(state)
    assert next_node == "product_manager"


def test_routing_market_fail_retries_under_cap(workflow):
    state: RunState = {
        "run_id": "r1",
        "idea": "Idea",
        "market": {},
        "prd": None,
        "architecture": None,
        "pitch": None,
        "scores": {"market": [5.5]},
        "debate_log": [],
        "retries": {"market": 0},
        "token_usage": {},
        "status": "running",
        "options": {"score_threshold": 7.0},
        "current_agent": "market_analyst",
        "errors": [],
        "debate_round": 0,
        "user_id": None,
        "_last_review": {"score": 5.5, "pass": False}
    }
    next_node = workflow.should_retry_market(state)
    assert next_node == "market_analyst"
    assert state["retries"]["market"] == 1


def test_routing_market_fail_advances_after_max_retries(workflow):
    state: RunState = {
        "run_id": "r1",
        "idea": "Idea",
        "market": {},
        "prd": None,
        "architecture": None,
        "pitch": None,
        "scores": {"market": [5.5, 6.0]},
        "debate_log": [],
        "retries": {"market": 2},  # Max retries reached
        "token_usage": {},
        "status": "running",
        "options": {"score_threshold": 7.0},
        "current_agent": "market_analyst",
        "errors": [],
        "debate_round": 0,
        "user_id": None,
        "_last_review": {"score": 6.0, "pass": False}
    }
    next_node = workflow.should_retry_market(state)
    # Failure handling: accept best version, advance to PM
    assert next_node == "product_manager"


def test_debate_routing_continues_when_unresolved(workflow):
    state: RunState = {
        "run_id": "r1",
        "idea": "Idea",
        "market": {},
        "prd": {},
        "architecture": {},
        "pitch": None,
        "scores": {},
        "debate_log": [],
        "retries": {},
        "token_usage": {},
        "status": "running",
        "options": {"debate_rounds": 2},
        "current_agent": None,
        "errors": [],
        "debate_round": 1,
        "_debate_resolved": False,
        "user_id": None
    }
    next_node = workflow.should_continue_debate(state)
    assert next_node == "debate_round"


def test_debate_routing_advances_when_resolved_or_max_rounds(workflow):
    state: RunState = {
        "run_id": "r1",
        "idea": "Idea",
        "market": {},
        "prd": {},
        "architecture": {},
        "pitch": None,
        "scores": {},
        "debate_log": [],
        "retries": {},
        "token_usage": {},
        "status": "running",
        "options": {"debate_rounds": 2},
        "current_agent": None,
        "errors": [],
        "debate_round": 2,  # Max 2 rounds
        "_debate_resolved": False,
        "user_id": None
    }
    next_node = workflow.should_continue_debate(state)
    assert next_node == "pitch_writer"
