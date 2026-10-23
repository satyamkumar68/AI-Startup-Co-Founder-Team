import json
from typing import Optional, Tuple, Dict, Any

from backend.app.agents.base import BaseAgent
from backend.app.models.schemas import CEOCriticReview
from backend.app.core.config import settings


class CEOCriticAgent(BaseAgent):
    """CEO / Critic Agent (AGENTS.md §5).
    
    Acts as the executive quality gatekeeper, evaluating any deliverable against
    institutional rubrics: Completeness, Specificity, Evidence, Feasibility, and Consistency.
    Scores 1.0 to 10.0 (pass threshold >= 7.0).
    """

    def __init__(
        self,
        model: Optional[str] = None,
        provider: Optional[str] = None,
        score_threshold: Optional[float] = None,
        **kwargs
    ):
        prov = provider or settings.LLM_PROVIDER
        if model:
            critic_model = model
        elif prov == "ollama":
            critic_model = "qwen2.5-coder:1.5b"
        else:
            critic_model = settings.MODEL_CRITIC
        super().__init__(
            name="CEO / Critic",
            prompt_file="ceo_critic.md",
            model=critic_model,
            provider=provider,
            **kwargs
        )
        self.score_threshold = score_threshold or settings.SCORE_THRESHOLD

    async def review(
        self,
        target_agent: str,
        deliverable_content: Dict[str, Any],
        version: int = 1,
        prior_context: Optional[Dict[str, Any]] = None
    ) -> Tuple[CEOCriticReview, Dict[str, Any]]:
        """Evaluate deliverable against rubric."""
        user_content = (
            f"Review Target Agent: {target_agent}\n"
            f"Deliverable Version: {version}\n\n"
            f"Deliverable Content to Evaluate:\n"
            f"{json.dumps(deliverable_content, indent=2)}\n\n"
        )
        if prior_context:
            user_content += (
                f"Prior Pipeline Context (for Consistency check):\n"
                f"{json.dumps(prior_context, indent=2)}\n\n"
            )

        user_content += (
            f"Please score this deliverable from 1.0 to 10.0 against the 5 rubric criteria:\n"
            f"1. Completeness\n"
            f"2. Specificity\n"
            f"3. Evidence / Grounding\n"
            f"4. Feasibility (<= 8 wks, 2 devs)\n"
            f"5. Consistency with prior deliverables\n\n"
            f"Minimum passing score is {self.score_threshold}."
        )

        review_obj, meta = await self.execute_structured(
            user_content=user_content,
            schema=CEOCriticReview,
            temperature=0.1
        )

        review_obj.target_agent = target_agent
        review_obj.version = version
        review_obj.pass_ = review_obj.score >= self.score_threshold

        return review_obj, meta
