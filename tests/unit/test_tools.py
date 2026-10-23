import pytest
from backend.app.tools.cost_estimator import CostEstimatorTool
from backend.app.tools.mermaid_validator import MermaidValidatorTool
from backend.app.tools.search import WebSearchTool


def test_cost_estimator_mvp():
    tool = CostEstimatorTool()
    res = tool.estimate(
        components=["Managed Web Service", "Managed PostgreSQL", "Managed Redis"],
        scale="mvp",
        include_ai_budget=True
    )
    assert res["total_usd"] > 0
    assert "breakdown" in res
    assert "assumptions" in res
    assert len(res["assumptions"]) > 0


def test_mermaid_validator_valid():
    tool = MermaidValidatorTool()
    valid_diagram = """
    flowchart TD
        A[Client] --> B[API Gateway]
        B --> C[(PostgreSQL)]
    """
    result = tool.validate(valid_diagram)
    assert result["valid"] is True
    assert len(result["issues"]) == 0


def test_mermaid_validator_invalid_type():
    tool = MermaidValidatorTool()
    invalid_diagram = "invalidType TD\n A --> B"
    result = tool.validate(invalid_diagram)
    assert result["valid"] is False
    assert len(result["issues"]) > 0


def test_mermaid_validator_sanitizes_arrows_and_spaces():
    tool = MermaidValidatorTool()
    # The exact pattern reported by the user in the screenshot
    problematic_diagram = """
    flowchart TD
        Client[Web Application] --> Gateway[API Gateway]
        Gateway --> EHR[EHR System]
        EHR → Patient Support[(Django)]
        Patient Support --> DB[(PostgreSQL)]
    """
    result = tool.validate(problematic_diagram)
    assert result["valid"] is True
    assert len(result["issues"]) == 0
    sanitized = result["sanitized_code"]
    assert "→" not in sanitized
    assert "EHR --> Patient_Support[(Django)]" in sanitized
    assert "Patient_Support --> DB[(PostgreSQL)]" in sanitized


@pytest.mark.asyncio
async def test_search_tool_caching():
    tool = WebSearchTool(provider="duckduckgo")
    # First call will execute or hit mock
    res1 = await tool.search("CBSE Class 10 edtech market", max_results=2)
    assert "results" in res1
    assert len(res1["results"]) > 0

    # Second identical query must hit cache
    res2 = await tool.search("CBSE Class 10 edtech market", max_results=2)
    assert res2["cached"] is True
