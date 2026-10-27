import os
from unittest.mock import patch
from backend.app.core.observability import setup_observability, log_execution_summary


def test_setup_observability_disabled():
    with patch.dict(os.environ, {"LANGSMITH_TRACING": "false", "LANGFUSE_PUBLIC_KEY": ""}, clear=True):
        status = setup_observability()
        assert status["tracing_active"] is False
        assert status["langsmith_enabled"] is False
        assert status["langfuse_enabled"] is False


def test_setup_observability_langsmith():
    with patch.dict(os.environ, {
        "LANGSMITH_TRACING": "true",
        "LANGSMITH_API_KEY": "ls_test_key_123",
        "LANGCHAIN_PROJECT": "test-project"
    }, clear=True):
        status = setup_observability()
        assert status["tracing_active"] is True
        assert status["langsmith_enabled"] is True
        assert os.environ.get("LANGCHAIN_TRACING_V2") == "true"


def test_log_execution_summary(caplog):
    telemetry = {
        "tokens": {"prompt": 1000, "completion": 500, "total": 1500},
        "cost_usd": 0.045,
        "latency_sec": 12.3,
        "schema_repairs": 1,
        "fallback_count": 0
    }
    with caplog.at_level("INFO"):
        log_execution_summary("run-abc", "multi_debate", telemetry)
    assert "[TELEMETRY]" in caplog.text
    assert "run_id=run-abc" in caplog.text
    assert "cost_usd=$0.0450" in caplog.text
