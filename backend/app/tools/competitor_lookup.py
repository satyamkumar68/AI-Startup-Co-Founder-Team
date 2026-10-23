from typing import List, Dict, Any
from backend.app.tools.search import WebSearchTool


class CompetitorLookupTool:
    """Tool to discover direct and indirect competitors for a given startup idea."""

    def __init__(self, search_tool: WebSearchTool):
        self.search_tool = search_tool

    async def lookup(self, idea: str, industry: str = "technology") -> Dict[str, Any]:
        """Perform targeted search queries for market competitors."""
        query = f"top competitors alternatives companies '{idea}' {industry}"
        search_data = await self.search_tool.search(query, max_results=6)
        
        return {
            "query": query,
            "raw_competitor_signals": search_data.get("results", []),
            "low_confidence": search_data.get("low_confidence", False)
        }
