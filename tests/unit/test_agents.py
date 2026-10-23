import pytest
from unittest.mock import AsyncMock, patch

from backend.app.agents.market_analyst import MarketAnalystAgent
from backend.app.agents.product_manager import ProductManagerAgent
from backend.app.agents.tech_architect import TechArchitectAgent
from backend.app.agents.pitch_writer import PitchWriterAgent
from backend.app.agents.ceo_critic import CEOCriticAgent
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


def test_agent_prompt_loading():
    analyst = MarketAnalystAgent(provider="ollama", model="qwen3:4b")
    assert "Market Analyst" in analyst.system_prompt

    pm = ProductManagerAgent(provider="openrouter", model="openai/gpt-4o")
    assert "Product Manager" in pm.system_prompt

    critic = CEOCriticAgent(provider="ollama", model="qwen3:4b")
    assert "CEO / Critic" in critic.system_prompt


@pytest.mark.asyncio
async def test_ceo_critic_evaluation():
    critic = CEOCriticAgent(provider="ollama", model="qwen3:4b", score_threshold=7.0)
    
    mock_review = CEOCriticReview(
        target_agent="market",
        version=1,
        score=8.5,
        strengths=["Clear addressable market sizing", "5 verified competitors"],
        weaknesses=["Regulatory timeline could be clearer"],
        required_changes=[],
        pass_=True
    )

    with patch.object(critic, "execute_structured", new_callable=AsyncMock) as mock_exec:
        mock_exec.return_value = (mock_review, {"tokens": 150, "latency_ms": 200})
        review, meta = await critic.review(
            target_agent="market",
            deliverable_content={"tam": "$10B"},
            version=1
        )
        assert review.score == 8.5
        assert review.pass_ is True
        assert review.target_agent == "market"
