import json
from typing import Optional, Tuple, Dict, Any, Union

from backend.app.agents.base import BaseAgent
from backend.app.models.schemas import (
    PitchWriterOutput,
    MarketAnalystOutput,
    ProductManagerOutput,
    TechArchitectOutput
)


class PitchWriterAgent(BaseAgent):
    """Pitch Writer Agent (AGENTS.md §4).
    
    Synthesizes market data, PRD features, and technical architecture into a
    compelling 10-12 slide investor pitch deck. Every claim must be backed by earlier outputs.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            name="Pitch Writer",
            prompt_file="pitch_writer.md",
            model=model,
            provider=provider,
            **kwargs
        )

    async def run(
        self,
        idea: str,
        market: Union[MarketAnalystOutput, Dict[str, Any]],
        prd: Union[ProductManagerOutput, Dict[str, Any]],
        architecture: Union[TechArchitectOutput, Dict[str, Any]]
    ) -> Tuple[PitchWriterOutput, Dict[str, Any]]:
        """Generate pitch deck from all prior deliverables."""
        market_dict = market.model_dump() if isinstance(market, MarketAnalystOutput) else market
        prd_dict = prd.model_dump() if isinstance(prd, ProductManagerOutput) else prd
        arch_dict = architecture.model_dump() if isinstance(architecture, TechArchitectOutput) else architecture

        user_content = (
            f"Startup Idea: {idea}\n\n"
            f"Market Intelligence:\n"
            f"- TAM: {market_dict.get('tam', {}).get('value', 'N/A')}\n"
            f"- SAM: {market_dict.get('sam', {}).get('value', 'N/A')}\n"
            f"- SOM: {market_dict.get('som', {}).get('value', 'N/A')}\n"
            f"- Competitors: {[c.get('name') if isinstance(c, dict) else getattr(c, 'name', '') for c in market_dict.get('competitors', [])]}\n\n"
            f"Product PRD:\n"
            f"- Problem Statement: {prd_dict.get('problem_statement', '')}\n"
            f"- MVP Scope: {prd_dict.get('mvp_scope', '')}\n"
            f"- Features: {[f.get('name') if isinstance(f, dict) else getattr(f, 'name', '') for f in prd_dict.get('features', [])]}\n\n"
            f"Technical Architecture:\n"
            f"- Stack: {[s.get('technology') if isinstance(s, dict) else getattr(s, 'technology', '') for s in arch_dict.get('stack', [])]}\n"
            f"- Monthly Run Rate: ${arch_dict.get('monthly_cost_estimate', {}).get('total_usd', 'N/A')}\n\n"
            f"Please write the 10-12 slide investor pitch deck.\n"
            f"Constraints:\n"
            f"- Exactly 10 to 12 slides\n"
            f"- No claim not backed by earlier deliverables\n"
            f"- Provide punchy bullets and detailed speaker notes for every slide"
        )

        return await self.execute_structured(
            user_content=user_content,
            schema=PitchWriterOutput,
            temperature=0.3
        )
