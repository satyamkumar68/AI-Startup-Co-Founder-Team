import pytest
from unittest.mock import AsyncMock, patch

from backend.app.graph.workflow import CoFounderWorkflow
from backend.app.models.state import RunState
from backend.app.agents.single_agent import SingleAgent, SingleAgentDeliverables
from backend.app.models.schemas import (
    MarketAnalystOutput,
    ProductManagerOutput,
    TechArchitectOutput,
    PitchWriterOutput
)


@pytest.fixture
def sample_deliverables():
    return SingleAgentDeliverables(
        market=MarketAnalystOutput(
            tam={"value": "$10B", "estimated": True, "source_url": "https://example.com"},
            sam={"value": "$2B", "estimated": True, "source_url": "https://example.com"},
            som={"value": "$100M", "estimated": True, "source_url": "https://example.com"},
            competitors=[
                {"name": f"Comp {i}", "description": "Desc", "strengths": ["S"], "weaknesses": ["W"]}
                for i in range(5)
            ],
            trends=["AI growth"],
            risks=["Risk 1", "Risk 2", "Risk 3"],
            sources=["https://example.com"]
        ),
        prd=ProductManagerOutput(
            problem_statement="Problem statement text",
            mvp_scope="MVP scope text",
            personas=[
                {"name": "Alice", "role": "User", "pain_points": ["Pain"], "goals": ["Goal"]},
                {"name": "Bob", "role": "Manager", "pain_points": ["Pain"], "goals": ["Goal"]}
            ],
            features=[{"name": "F1", "priority": "P0"}],
            user_stories=["As user I want X", "As user I want Y", "As user I want Z"],
            success_metrics=["Metric 1 (70% retention)", "Metric 2 (15% growth)"]
        ),
        architecture=TechArchitectOutput(
            stack=[{"technology": "Python", "category": "Backend", "justification": "Fast"}],
            components=[{"name": "API", "responsibility": "Routing", "technologies": ["FastAPI"]}],
            diagram_mermaid="graph TD; A-->B;",
            data_model="SQL",
            scalability_notes="Dockerized",
            monthly_cost_estimate={"total_usd": 50.0, "breakdown": {"compute": 50.0}, "assumptions": ["Assumed"]},
            risks=["Risk"]
        ),
        pitch=PitchWriterOutput(
            slides=[
                {"slide_number": i + 1, "title": f"Slide {i + 1}", "bullets": ["B1", "B2"], "speaker_notes": "Note"}
                for i in range(10)
            ]
        )
    )


def test_workflow_mode_initialization():
    wf_single = CoFounderWorkflow(mode="single_agent")
    assert wf_single.mode == "single_agent"

    wf_nodebate = CoFounderWorkflow(mode="multi_no_debate")
    assert wf_nodebate.mode == "multi_no_debate"

    wf_debate = CoFounderWorkflow(mode="multi_debate")
    assert wf_debate.mode == "multi_debate"


def test_route_after_intake():
    wf = CoFounderWorkflow(mode="multi_debate")

    state_single: RunState = {"run_id": "1", "idea": "Test", "mode": "single_agent"}
    assert wf.route_after_intake(state_single) == "single_agent"

    state_debate: RunState = {"run_id": "2", "idea": "Test", "mode": "multi_debate"}
    assert wf.route_after_intake(state_debate) == "market_analyst"

    state_no_debate: RunState = {"run_id": "3", "idea": "Test", "mode": "multi_no_debate"}
    assert wf.route_after_intake(state_no_debate) == "market_analyst"


def test_multi_no_debate_router_bypass():
    wf = CoFounderWorkflow(mode="multi_no_debate")
    state: RunState = {
        "run_id": "1",
        "idea": "Test",
        "mode": "multi_no_debate",
        "scores": {"market": [5.0], "prd": [4.0], "architecture": [3.0], "pitch": [4.0]},
        "retries": {"market": 0, "prd": 0, "architecture": 0, "pitch": 0}
    }

    # In multi_no_debate mode, routers immediately advance without retry loops or debate
    assert wf.should_retry_market(state) == "product_manager"
    assert wf.should_retry_pm(state) == "tech_architect"
    assert wf.should_retry_architect(state) == "pitch_writer"
    assert wf.should_retry_pitch(state) == "finalize"


@pytest.mark.asyncio
async def test_single_agent_node_execution(sample_deliverables):
    wf = CoFounderWorkflow(mode="single_agent")
    state: RunState = {
        "run_id": "sa-001",
        "idea": "An AI platform for automated test scoring",
        "mode": "single_agent",
        "telemetry": {
            "start_time": 1000.0,
            "tokens": {"prompt": 0, "completion": 0, "total": 0},
            "cost_usd": 0.0,
            "schema_repairs": 0,
            "fallback_count": 0
        }
    }

    mock_meta = {
        "tokens": 4200,
        "prompt_tokens": 1200,
        "completion_tokens": 3000,
        "cost_usd": 0.015,
        "schema_repairs": 0,
        "fallback_count": 0
    }

    with patch.object(SingleAgent, "run", new_callable=AsyncMock) as mock_run:
        mock_run.return_value = (sample_deliverables, mock_meta)
        result = await wf.single_agent_node(state)

        assert "market" in result
        assert "prd" in result
        assert "architecture" in result
        assert "pitch" in result
        assert result["token_usage"]["total"] == 4200
        assert result["telemetry"]["tokens"]["total"] == 4200
        assert result["telemetry"]["cost_usd"] == 0.015
        assert result["current_agent"] == "single_agent"


@pytest.mark.asyncio
async def test_finalize_node_computes_telemetry():
    wf = CoFounderWorkflow(mode="single_agent")
    state: RunState = {
        "run_id": "test-fin",
        "idea": "Sample",
        "retries": {"market": 1, "prd": 0, "architecture": 0, "pitch": 0},
        "telemetry": {
            "start_time": 100.0,
            "tokens": {"prompt": 500, "completion": 500, "total": 1000},
            "cost_usd": 0.005,
            "schema_repairs": 1,
            "fallback_count": 0
        }
    }

    result = await wf.finalize_node(state)
    assert result["status"] == "completed"
    assert "telemetry" in result
    assert result["telemetry"]["retries"] == 1
    assert result["telemetry"]["latency_sec"] > 0
