import json
from typing import Optional, Tuple, Dict, Any

from backend.app.agents.base import BaseAgent
from backend.app.models.schemas import MarketAnalystOutput
from backend.app.tools.search import WebSearchTool
from backend.app.tools.competitor_lookup import CompetitorLookupTool


class MarketAnalystAgent(BaseAgent):
    """Market Analyst Agent (AGENTS.md §1).
    
    Conducts web searches for market sizing, competitor intel, trends, and risks.
    Outputs structured MarketAnalystOutput.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        search_tool: Optional[WebSearchTool] = None,
        **kwargs
    ):
        super().__init__(
            name="Market Analyst",
            prompt_file="market_analyst.md",
            model=model,
            provider=provider,
            **kwargs
        )
        self.search_tool = search_tool or WebSearchTool()
        self.competitor_tool = CompetitorLookupTool(self.search_tool)

    async def run(self, idea: str) -> Tuple[MarketAnalystOutput, Dict[str, Any]]:
        """Execute market analysis for the startup idea."""
        # 1. Perform web search for TAM / market sizing
        market_search = await self.search_tool.search(f"{idea} market size industry report TAM", max_results=4)
        
        # 2. Perform competitor lookup
        competitor_search = await self.competitor_tool.lookup(idea)

        # 3. Assemble research context for the prompt (compacted for fast local inference)
        compact_market = [
            {"title": r.get("title", ""), "snippet": r.get("snippet", "")[:160], "url": r.get("url", "")}
            for r in market_search.get("results", [])[:3]
        ]
        compact_competitors = [
            {"name": c.get("name", ""), "snippet": c.get("snippet", "")[:160], "url": c.get("url", "")}
            for c in competitor_search.get("raw_competitor_signals", [])[:4]
        ]

        research_context = (
            f"Startup Idea: {idea}\n\n"
            f"Market Intelligence Web Search Signals:\n"
            f"{json.dumps(compact_market, separators=(',', ':'))}\n\n"
            f"Competitor Intelligence Signals:\n"
            f"{json.dumps(compact_competitors, separators=(',', ':'))}\n"
        )

        user_content = (
            f"Please conduct an in-depth market analysis for this startup idea.\n\n"
            f"{research_context}\n"
            f"Remember:\n"
            f"- At least 5 competitors with strengths and weaknesses\n"
            f"- At least 3 risks\n"
            f"- Every TAM/SAM/SOM number must have a source_url and 'estimated': true if derived"
        )

        output, meta = await self.execute_structured(
            user_content=user_content,
            schema=MarketAnalystOutput,
            temperature=0.2
        )

        if market_search.get("low_confidence") or competitor_search.get("low_confidence"):
            meta["low_confidence"] = True

        return output, meta
