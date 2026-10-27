import os
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


def setup_observability() -> Dict[str, Any]:
    """Configure optional distributed tracing (LangSmith / Langfuse / OpenTelemetry).
    
    Automatically activates tracing when corresponding environment variables are present.
    Safe no-op if tracing credentials are not supplied.
    """
    status: Dict[str, Any] = {
        "langsmith_enabled": False,
        "langfuse_enabled": False,
        "tracing_active": False
    }

    # 1. Check LangSmith Configuration
    langsmith_env = os.getenv("LANGSMITH_TRACING", "").lower() in ("true", "1", "yes")
    langsmith_key = os.getenv("LANGSMITH_API_KEY", "") or os.getenv("LANGCHAIN_API_KEY", "")

    if langsmith_env and langsmith_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_PROJECT"] = os.getenv("LANGCHAIN_PROJECT", "ai-startup-cofounder")
        status["langsmith_enabled"] = True
        status["tracing_active"] = True
        logger.info(f"LangSmith distributed tracing active (project: {os.environ['LANGCHAIN_PROJECT']})")

    # 2. Check Langfuse Configuration
    langfuse_key = os.getenv("LANGFUSE_PUBLIC_KEY", "")
    if langfuse_key:
        status["langfuse_enabled"] = True
        status["tracing_active"] = True
        logger.info("Langfuse observability integration configured")

    if not status["tracing_active"]:
        logger.debug("Observability tracing disabled (no LANGSMITH_API_KEY or LANGFUSE_PUBLIC_KEY provided)")

    return status


def log_execution_summary(run_id: str, mode: str, telemetry: Dict[str, Any]) -> None:
    """Log structured execution summary with telemetry metrics for monitoring."""
    tokens = telemetry.get("tokens", {})
    cost = telemetry.get("cost_usd", 0.0)
    latency = telemetry.get("latency_sec", 0.0)
    repairs = telemetry.get("schema_repairs", 0)
    fallbacks = telemetry.get("fallback_count", 0)

    logger.info(
        f"[TELEMETRY] run_id={run_id} mode={mode} latency={latency}s "
        f"tokens_total={tokens.get('total', 0)} (prompt={tokens.get('prompt', 0)}, comp={tokens.get('completion', 0)}) "
        f"cost_usd=${cost:.4f} schema_repairs={repairs} fallbacks={fallbacks}"
    )
