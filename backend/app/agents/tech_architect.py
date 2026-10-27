import json
from typing import Optional, Tuple, Dict, Any, Union

from backend.app.agents.base import BaseAgent
from backend.app.models.schemas import (
    TechArchitectOutput,
    MarketAnalystOutput,
    ProductManagerOutput,
    MonthlyCostEstimate
)
from backend.app.tools.cost_estimator import CostEstimatorTool
from backend.app.tools.mermaid_validator import MermaidValidatorTool


class TechArchitectAgent(BaseAgent):
    """Tech Architect Agent (AGENTS.md §3).
    
    Designs the technical architecture, chooses a pragmatic stack with 1-line justifications,
    generates a valid Mermaid diagram, and estimates monthly cloud expenditure.
    """

    def __init__(
        self,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        cost_tool: Optional[CostEstimatorTool] = None,
        mermaid_tool: Optional[MermaidValidatorTool] = None,
        **kwargs
    ):
        super().__init__(
            name="Tech Architect",
            prompt_file="tech_architect.md",
            model=model,
            provider=provider,
            **kwargs
        )
        self.cost_tool = cost_tool or CostEstimatorTool()
        self.mermaid_tool = mermaid_tool or MermaidValidatorTool()

    async def run(
        self,
        idea: str,
        market: Union[MarketAnalystOutput, Dict[str, Any]],
        prd: Union[ProductManagerOutput, Dict[str, Any]],
        founder_guidance: Optional[str] = None
    ) -> Tuple[TechArchitectOutput, Dict[str, Any]]:
        """Generate architectural specifications from idea, market, and PRD."""
        market_dict = market.model_dump() if isinstance(market, MarketAnalystOutput) else market
        prd_dict = prd.model_dump() if isinstance(prd, ProductManagerOutput) else prd

        p0_features = [
            f.get("name") if isinstance(f, dict) else getattr(f, "name", "")
            for f in prd_dict.get("features", [])
            if (f.get("priority") if isinstance(f, dict) else getattr(f, "priority", "")) == "P0"
        ]

        # Use cost estimator benchmark guidance
        cost_benchmark = self.cost_tool.estimate(
            components=["Managed Web Service", "Managed PostgreSQL", "Managed Redis", "S3 Storage"]
        )

        user_content = (
            f"Startup Idea: {idea}\n\n"
            f"PRD Problem Statement: {prd_dict.get('problem_statement', '')}\n"
            f"MVP Scope: {prd_dict.get('mvp_scope', '')}\n"
            f"Core P0 Features to Support:\n{json.dumps(p0_features, indent=2)}\n\n"
            f"Baseline Cost Guidance:\n{json.dumps(cost_benchmark, indent=2)}\n\n"
            f"Please design the technical architecture.\n"
            f"Constraints:\n"
            f"- Justify every stack choice in one line\n"
            f"- Prefer managed services for MVP speed\n"
            f"- Valid Mermaid flowchart diagram\n"
            f"- Sane monthly cost estimate"
        )
        if founder_guidance:
            user_content += f"\n\nFounder Steering / Review Notes to Incorporate:\n{founder_guidance}"

        output, meta = await self.execute_structured(
            user_content=user_content,
            schema=TechArchitectOutput,
            temperature=0.2
        )

        # Validate and sanitize Mermaid diagram
        mermaid_check = self.mermaid_tool.validate(output.diagram_mermaid)
        if not mermaid_check.get("valid"):
            # Provide clean fallback diagram if model hallucinated invalid syntax
            output.diagram_mermaid = (
                "flowchart TD\n"
                "    Client[Web Client] --> API[FastAPI App]\n"
                "    API --> Worker[Redis Worker]\n"
                "    Worker --> DB[(PostgreSQL)]\n"
                "    Worker --> LLM[LLM Provider]"
            )
        else:
            output.diagram_mermaid = mermaid_check.get("sanitized_code", output.diagram_mermaid)

        return output, meta
