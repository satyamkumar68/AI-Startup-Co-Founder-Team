import pytest
from backend.app.models.schemas import MarketMetric, MarketAnalystOutput
from backend.app.tools.cost_estimator import CostEstimatorTool
from backend.app.graph.fact_check import FactCheckEngine


def test_market_metric_grounding_validation():
    # 1. Fully grounded metric with verified URL
    grounded = MarketMetric(
        value="$12.4B",
        unit="USD",
        source_url="https://gartner.com/reports/market-sizing",
        retrieved_at="2026-10-27"
    )
    assert grounded.is_assumption is False
    assert grounded.source_url == "https://gartner.com/reports/market-sizing"
    assert grounded.retrieved_at == "2026-10-27"

    # 2. Metric without URL automatically flagged as an assumption
    assumed = MarketMetric(
        value="$500M",
        unit="USD"
    )
    assert assumed.is_assumption is True
    assert assumed.retrieved_at is not None

    # 3. String auto-parser handles raw string and flags as assumption
    parsed_from_str = MarketMetric.parse_from_string("$2.1B")
    metric = MarketMetric(**parsed_from_str)
    assert metric.is_assumption is True


def test_pinned_cloud_cost_estimator():
    tool = CostEstimatorTool()
    components = ["Managed Web Service", "Managed PostgreSQL", "Serverless Redis", "LLM API Tokens"]
    result = tool.estimate(components, scale="mvp")

    assert "total_usd" in result
    assert result["total_usd"] > 0
    assert "sources" in result
    assert result["estimate_unverified"] is False
    assert "data/cloud_pricing.json" in result["assumptions"][0]

    # Test unknown component triggers estimate_unverified flag
    unverified_res = tool.estimate(["Quantum Supercomputer Hosting"], scale="mvp")
    assert unverified_res["estimate_unverified"] is True
    assert any("estimate_unverified" in a for a in unverified_res["assumptions"])


def test_fact_check_engine_audit():
    engine = FactCheckEngine()
    state = {
        "market": {
            "tam": {"value": "$10B", "source_url": "https://bloomberg.com/news", "is_assumption": False, "retrieved_at": "2026-10-27"},
            "sam": {"value": "$2B", "source_url": None, "is_assumption": True, "retrieved_at": "2026-10-27"},
            "som": {"value": "$150M", "source_url": None, "is_assumption": False, "retrieved_at": "2026-10-27"}
        },
        "architecture": {
            "monthly_cost_estimate": {
                "total_usd": 68.0,
                "breakdown": {"Managed Web Service": 7.0, "Managed PostgreSQL": 19.0},
                "sources": {"Managed Web Service": "https://render.com/pricing", "Managed PostgreSQL": "https://neon.tech/pricing"},
                "estimate_unverified": False
            }
        }
    }

    report = engine.verify(state)
    assert report["verified_count"] >= 3
    assert report["assumption_count"] >= 1
    # som has no url and is_assumption was false, so it must be flagged as ungrounded!
    assert report["unverified_count"] >= 1
    assert len(report["flagged_claims"]) >= 1
    assert "Verification & Sourcing Appendix" in report["appendix_markdown"]
    assert "UNGROUNDED CLAIM" in report["appendix_markdown"]
