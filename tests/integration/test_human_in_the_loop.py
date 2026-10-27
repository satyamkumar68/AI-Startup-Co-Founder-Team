import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from langgraph.types import Command

from backend.app.main import app
from backend.app.graph.workflow import CoFounderWorkflow
from backend.app.worker import ACTIVE_WORKFLOWS, resume_run_pipeline
from backend.app.models.schemas import (
    MarketAnalystOutput,
    ProductManagerOutput,
    TechArchitectOutput,
    PitchWriterOutput,
    CEOCriticReview,
    FeatureItem,
    Persona,
    StackChoice,
    ArchitectureComponent,
    MonthlyCostEstimate,
    PitchSlide
)


def _mock_market():
    return MarketAnalystOutput(
        tam={"value": "$10B", "source_url": "https://statista.com/market", "is_assumption": False},
        sam={"value": "$1B", "source_url": "https://gartner.com/sam", "is_assumption": False},
        som={"value": "$100M", "source_url": "https://internal.report/som", "is_assumption": False},
        competitors=[
            {"name": f"Comp{i}", "description": "desc", "strengths": ["s"], "weaknesses": ["w"]}
            for i in range(5)
        ],
        trends=["trend1"],
        risks=["risk1", "risk2", "risk3"],
        sources=["https://statista.com/market"]
    )


def _mock_prd():
    return ProductManagerOutput(
        personas=[
            Persona(name="Dev Lead", role="Lead", pain_points=["context switching"], goals=["ship faster"]),
            Persona(name="Engineer", role="Dev", pain_points=["slow reviews"], goals=["clean code"])
        ],
        problem_statement="Engineers spend 40% of time in review bottlenecks.",
        features=[FeatureItem(name="Core Copilot", priority="P0", description="Core feature")],
        mvp_scope="Build in 6 weeks with 2 engineers",
        user_stories=[
            "As a dev, I want instant reviews so that I unblock teammates.",
            "As a lead, I want PR summaries so that I review faster.",
            "As an eng, I want automated test checks so that regressions drop."
        ],
        success_metrics=["MAU > 1000", "Review latency < 1h"]
    )


def _mock_arch():
    return TechArchitectOutput(
        stack=[
            StackChoice(technology="FastAPI", category="Backend", justification="Async performance"),
            StackChoice(technology="PostgreSQL", category="Database", justification="ACID compliance")
        ],
        components=[
            ArchitectureComponent(name="API Gateway", responsibility="Routing", technologies=["FastAPI"])
        ],
        diagram_mermaid="graph TD;\n  Client-->API;\n  API-->DB;",
        data_model="erDiagram USER ||--o{ REPO : owns",
        scalability_notes="Horizontal worker scaling",
        monthly_cost_estimate=MonthlyCostEstimate(
            total_usd=85.0,
            breakdown={"database": 25.0, "compute": 60.0},
            assumptions=["100 concurrent users"]
        ),
        risks=["DB connection pooling spikes", "LLM latency"]
    )


def _mock_pitch():
    return PitchWriterOutput(
        slides=[
            PitchSlide(slide_number=i, title=f"Slide {i}", bullets=["point 1", "point 2"], speaker_notes="notes")
            for i in range(1, 11)
        ],
        elevator_pitch="Transforming developer workflows."
    )


def _mock_review_pass(target="prd"):
    return CEOCriticReview(
        target_agent=target,
        score=8.5,
        pass_=True,
        strengths=["Solid coverage"],
        weaknesses=[],
        required_changes=[]
    )


@pytest.mark.asyncio
async def test_workflow_bypasses_human_review_when_disabled():
    workflow = CoFounderWorkflow(provider="ollama", model_default="llama3.2")
    
    with patch.object(workflow.market_agent, "run", return_value=(_mock_market(), {"tokens": 100})), \
         patch.object(workflow.pm_agent, "run", return_value=(_mock_prd(), {"tokens": 100})), \
         patch.object(workflow.architect_agent, "run", return_value=(_mock_arch(), {"tokens": 100})), \
         patch.object(workflow.pitch_agent, "run", return_value=(_mock_pitch(), {"tokens": 100})), \
         patch.object(workflow.critic_agent, "review", return_value=(_mock_review_pass(), {"tokens": 50})):

        state = {
            "run_id": "test_no_hitl",
            "idea": "An AI copilot for distributed dev teams.",
            "status": "pending",
            "options": {"enable_human_review": False, "debate_rounds": 0},
            "token_usage": {"total": 0},
            "scores": {},
            "retries": {}
        }
        res = await workflow.graph.ainvoke(state, config={"configurable": {"thread_id": "test_no_hitl"}})
        assert "__interrupt__" not in res
        assert res["status"] == "completed"
        assert res["prd"] is not None
        assert res["architecture"] is not None


@pytest.mark.asyncio
async def test_workflow_pauses_and_resumes_with_human_edits():
    workflow = CoFounderWorkflow(provider="ollama", model_default="llama3.2")
    run_id = "test_hitl_pause_resume"

    with patch.object(workflow.market_agent, "run", return_value=(_mock_market(), {"tokens": 100})), \
         patch.object(workflow.pm_agent, "run", return_value=(_mock_prd(), {"tokens": 100})), \
         patch.object(workflow.architect_agent, "run", return_value=(_mock_arch(), {"tokens": 100})), \
         patch.object(workflow.pitch_agent, "run", return_value=(_mock_pitch(), {"tokens": 100})), \
         patch.object(workflow.critic_agent, "review", return_value=(_mock_review_pass(), {"tokens": 50})):

        state = {
            "run_id": run_id,
            "idea": "A collaborative dev tool.",
            "status": "pending",
            "options": {"enable_human_review": True, "debate_rounds": 0},
            "token_usage": {"total": 0},
            "scores": {},
            "retries": {}
        }

        config = {"configurable": {"thread_id": run_id}}
        res1 = await workflow.graph.ainvoke(state, config=config)

        # Confirm paused at interrupt
        assert "__interrupt__" in res1
        interrupt_payload = res1["__interrupt__"][0].value
        assert interrupt_payload["type"] == "human_review"
        assert interrupt_payload["target"] == "prd"

        # Check pending tasks in state snapshot
        snapshot = await workflow.graph.aget_state(config)
        assert len(snapshot.tasks) > 0

        # Now resume with edited PRD
        edited_prd = _mock_prd().model_dump()
        edited_prd["features"][0]["name"] = "Human Approved Feature Name"

        resume_payload = {
            "approved": True,
            "edited_prd": edited_prd,
            "feedback": "Approved with modified title"
        }

        res2 = await workflow.graph.ainvoke(Command(resume=resume_payload), config=config)
        assert res2["status"] == "completed"
        assert res2["prd"]["features"][0]["name"] == "Human Approved Feature Name"
        assert any("Human reviewer feedback" in err for err in res2.get("errors", []))


def test_api_pending_and_resume_endpoints():
    client = TestClient(app)
    run_id = "test_api_hitl_run"

    # 1. When not in ACTIVE_WORKFLOWS and not in DB
    resp = client.get(f"/api/v1/runs/{run_id}/pending")
    assert resp.status_code == 200
    assert resp.json()["awaiting_approval"] is False

    # 2. Register mock interrupted workflow entry
    mock_workflow = MagicMock()
    mock_workflow.graph.ainvoke = MagicMock()
    ACTIVE_WORKFLOWS[run_id] = {
        "workflow": mock_workflow,
        "options": {"enable_human_review": True},
        "event_broadcaster": MagicMock(),
        "state": {
            "run_id": run_id,
            "prd": {"features": [{"name": "Original"}]},
            "__interrupt__": [MagicMock(value={"type": "human_review", "target": "prd"})]
        }
    }

    resp = client.get(f"/api/v1/runs/{run_id}/pending")
    assert resp.status_code == 200
    data = resp.json()
    assert data["awaiting_approval"] is True
    assert data["prd"]["features"][0]["name"] == "Original"

    # 3. Call POST resume endpoint
    resume_req = {
        "approved": True,
        "edited_prd": {"features": [{"name": "Edited by User"}]},
        "feedback": "LGTM!"
    }
    with patch("backend.app.worker.resume_run_pipeline") as mock_resume_pipe:
        resp = client.post(f"/api/v1/runs/{run_id}/resume", json=resume_req)
        assert resp.status_code == 200
        assert resp.json()["status"] == "running"

    # Clean up
    ACTIVE_WORKFLOWS.pop(run_id, None)
