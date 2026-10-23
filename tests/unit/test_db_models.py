import uuid
from backend.app.models.db import User, Run, AgentOutput, Score, DebateMessage, Export, Base


def test_db_models_table_names():
    assert User.__tablename__ == "users"
    assert Run.__tablename__ == "runs"
    assert AgentOutput.__tablename__ == "agent_outputs"
    assert Score.__tablename__ == "scores"
    assert DebateMessage.__tablename__ == "debate_messages"
    assert Export.__tablename__ == "exports"


def test_run_model_instantiation():
    run_id = uuid.uuid4()
    run = Run(
        id=run_id,
        idea="AI tutor for Class 10 students in India",
        status="queued",
        options={"debate_rounds": 2, "score_threshold": 7.0},
        total_tokens=0,
        total_cost_usd=0.0
    )
    assert run.id == run_id
    assert run.status == "queued"
    assert run.options["debate_rounds"] == 2
