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
async def test_search_tool_caching(monkeypatch):
    tool = WebSearchTool(provider="duckduckgo")
    mock_results = [
        {"title": "CBSE Edtech Market", "href": "https://example.com/edtech", "url": "https://example.com/edtech", "body": "Market data", "snippet": "Market data"}
    ]
    async def mock_execute(query, max_results):
        return mock_results
    monkeypatch.setattr(tool, "_execute_search", mock_execute)

    # First call will execute and populate cache
    res1 = await tool.search("CBSE Class 10 edtech market", max_results=2)
    assert "results" in res1
    assert len(res1["results"]) > 0
    assert res1.get("cached") is False

    # Second identical query must hit cache without invoking search provider
    async def should_not_be_called(query, max_results):
        raise AssertionError("_execute_search should not be called on cache hit")
    monkeypatch.setattr(tool, "_execute_search", should_not_be_called)

    res2 = await tool.search("CBSE Class 10 edtech market", max_results=2)
    assert res2["cached"] is True
    assert res2["results"] == mock_results
