import json
from typing import Optional, Tuple, Dict, Any, Union

from backend.app.agents.base import BaseAgent
from backend.app.models.schemas import ProductManagerOutput, MarketAnalystOutput


class ProductManagerAgent(BaseAgent):
    """Product Manager Agent (AGENTS.md §2).
    
    Synthesizes the idea and market analysis into a razor-sharp PRD,
    enforcing a strict MVP boundary (<= 8 weeks, 2 devs, max 8 P0 features).
    """

    def __init__(
        self,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            name="Product Manager",
            prompt_file="product_manager.md",
            model=model,
            provider=provider,
            **kwargs
        )

    async def run(
        self,
        idea: str,
        market: Union[MarketAnalystOutput, Dict[str, Any]]
    ) -> Tuple[ProductManagerOutput, Dict[str, Any]]:
        """Generate PRD from idea and market analysis."""
        market_dict = market.model_dump() if isinstance(market, MarketAnalystOutput) else market

        user_content = (
            f"Startup Idea: {idea}\n\n"
            f"Market Analysis Findings:\n"
            f"TAM: {market_dict.get('tam', {}).get('value', 'N/A')}\n"
            f"Competitors: {[c.get('name') if isinstance(c, dict) else getattr(c, 'name', '') for c in market_dict.get('competitors', [])]}\n"
            f"Key Trends: {market_dict.get('trends', [])}\n"
            f"Identified Market Risks: {market_dict.get('risks', [])}\n\n"
            f"Please generate the complete Product Requirements Document (PRD).\n"
            f"Constraints:\n"
            f"- At least 2 distinct user personas\n"
            f"- Max 8 P0 features\n"
            f"- MVP must be buildable in <= 8 weeks by a 2-person engineering team"
        )

        return await self.execute_structured(
            user_content=user_content,
            schema=ProductManagerOutput,
            temperature=0.2
        )
