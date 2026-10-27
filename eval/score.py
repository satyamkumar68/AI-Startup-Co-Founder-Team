import os
import json
import logging
from typing import Dict, Any, List, Optional, Literal, Tuple
from pydantic import BaseModel, Field

from backend.app.agents.llm import MultiProviderLLM, LLMResponse, extract_json_from_text
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class RubricBreakdown(BaseModel):
    """5-dimension rubric score (1.0 - 5.0 scale) defined in AGENTS.md / SKILL.md."""
    market_realism: float = Field(..., ge=1.0, le=5.0, description="Mathematical sanity of TAM/SAM/SOM and competitor credibility")
    internal_consistency: float = Field(..., ge=1.0, le=5.0, description="PRD features map to architecture; TAM math aligns with target persona")
    feasibility_cost: float = Field(..., ge=1.0, le=5.0, description="Plausibility of cloud architecture, tech stack, and monthly cost")
    specificity: float = Field(..., ge=1.0, le=5.0, description="Concrete metrics, user stories, and acceptance criteria vs generic buzzwords")
    risk_awareness: float = Field(..., ge=1.0, le=5.0, description="Identification of critical regulatory, operational, churn, and security vulnerabilities")
    
    rationale: Dict[str, str] = Field(default_factory=dict, description="Brief justification for each dimension score")

    @property
    def composite_10(self) -> float:
        """Normalized overall score on 10.0 scale."""
        avg_5 = (self.market_realism + self.internal_consistency + self.feasibility_cost + self.specificity + self.risk_awareness) / 5.0
        return round(avg_5 * 2.0, 2)


class PairwiseComparison(BaseModel):
    """Pairwise winner determination between two execution modes."""
    winner: Literal["A", "B", "TIE"] = Field(..., description="Chosen superior output or tie")
    margin: Literal["slight", "clear", "decisive"] = Field(default="clear")
    key_reasons: List[str] = Field(default_factory=list, description="Primary reasons for decision")


class EvaluationJudge:
    """Independent LLM Judge evaluating deliverable quality across standard rubric.
    
    Adheres strictly to SKILL:
    - Never invent metrics.
    - Evaluates on 5 core dimensions: market realism, consistency, feasibility, specificity, risks.
    - Uses a distinct model family where possible to prevent self-preference bias.
    """

    def __init__(
        self,
        judge_model: Optional[str] = None,
        provider: Optional[str] = None
    ):
        self.provider = provider or ("gemini" if settings.GEMINI_API_KEY else settings.LLM_PROVIDER)
        self.model = judge_model or settings.MODEL_CRITIC
        self.llm = MultiProviderLLM(
            provider=self.provider,
            model=self.model,
            timeout=120.0
        )

    async def score_deliverables(self, deliverables: Dict[str, Any], idea: str) -> RubricBreakdown:
        """Evaluate a full deliverable package using LLM judge with heuristic fallback."""
        market = deliverables.get("market") or {}
        prd = deliverables.get("prd") or {}
        arch = deliverables.get("architecture") or {}
        pitch = deliverables.get("pitch") or {}

        judge_prompt = (
            f"You are an impartial, highly rigorous Venture Capital Principal and Technical Evaluator.\n"
            f"Please score the following startup deliverables generated for this idea:\n"
            f"IDEA: {idea}\n\n"
            f"DELIVERABLES:\n"
            f"- Market Analysis: {json.dumps(market, default=str)[:1200]}\n"
            f"- PRD: {json.dumps(prd, default=str)[:1200]}\n"
            f"- Architecture: {json.dumps(arch, default=str)[:1200]}\n"
            f"- Pitch Deck: {json.dumps(pitch, default=str)[:1200]}\n\n"
            f"RUBRIC CRITERIA (Rate each 1.0 to 5.0):\n"
            f"1. market_realism: Are TAM/SAM/SOM numbers grounded and mathematically sound? Are competitors real?\n"
            f"2. internal_consistency: Does architecture actually support the PRD features? Does pricing match personas?\n"
            f"3. feasibility_cost: Is the monthly cost realistic ($20-$500/mo for MVP) and stack reasonable?\n"
            f"4. specificity: Are personas, features, and metrics concrete, or generic fluff?\n"
            f"5. risk_awareness: Are severe technical, regulatory, or distribution failure points identified?\n\n"
            f"Output strictly a JSON matching the RubricBreakdown schema."
        )

        messages = [
            {"role": "system", "content": "You are a precise, objective venture evaluation judge."},
            {"role": "user", "content": judge_prompt}
        ]

        try:
            resp = await self.llm.generate_structured(messages, schema=RubricBreakdown, temperature=0.1)
            if resp.parsed:
                return resp.parsed
        except Exception as e:
            logger.warning(f"LLM Judge scoring failed ({e}); falling back to deterministic heuristic rubric.")

        return self.heuristic_score(deliverables)

    def heuristic_score(self, deliverables: Dict[str, Any]) -> RubricBreakdown:
        """Deterministic heuristic scoring engine for offline/test environments."""
        market = deliverables.get("market") or {}
        prd = deliverables.get("prd") or {}
        arch = deliverables.get("architecture") or {}
        pitch = deliverables.get("pitch") or {}

        # 1. Market Realism (1-5)
        m_score = 3.0
        tam_url = market.get("tam", {}).get("source_url")
        if tam_url and "http" in str(tam_url):
            m_score += 1.0
        if len(market.get("competitors", [])) >= 5:
            m_score += 0.5
        if len(market.get("risks", [])) >= 3:
            m_score += 0.5
        m_score = min(5.0, max(1.0, m_score))

        # 2. Internal Consistency (1-5)
        c_score = 3.5
        if prd.get("features") and arch.get("components"):
            c_score += 0.5
        if prd.get("personas") and len(prd.get("personas")) >= 2:
            c_score += 0.5
        c_score = min(5.0, max(1.0, c_score))

        # 3. Feasibility & Cost (1-5)
        f_score = 3.0
        cost_info = arch.get("monthly_cost_estimate") or {}
        tot = cost_info.get("total_usd", 0.0)
        if 15.0 <= tot <= 500.0:
            f_score += 1.0
        if cost_info.get("breakdown"):
            f_score += 0.5
        f_score = min(5.0, max(1.0, f_score))

        # 4. Specificity (1-5)
        s_score = 3.0
        if len(prd.get("user_stories", [])) >= 3:
            s_score += 0.5
        if len(prd.get("success_metrics", [])) >= 2:
            s_score += 0.5
        if len(pitch.get("slides", [])) >= 10:
            s_score += 0.5
        s_score = min(5.0, max(1.0, s_score))

        # 5. Risk Awareness (1-5)
        r_score = 3.0
        r_count = len(market.get("risks", [])) + len(arch.get("risks", []))
        if r_count >= 4:
            r_score += 1.0
        if r_count >= 6:
            r_score += 0.5
        r_score = min(5.0, max(1.0, r_score))

        return RubricBreakdown(
            market_realism=round(m_score, 1),
            internal_consistency=round(c_score, 1),
            feasibility_cost=round(f_score, 1),
            specificity=round(s_score, 1),
            risk_awareness=round(r_score, 1),
            rationale={
                "market_realism": "Evaluated based on source citations and competitor counts",
                "internal_consistency": "Evaluated based on persona and component alignment",
                "feasibility_cost": "Evaluated based on monthly cost estimate plausibility",
                "specificity": "Evaluated based on user stories, metrics, and slide counts",
                "risk_awareness": "Evaluated based on total identified market and tech risks"
            }
        )

    async def compare_pairwise(
        self,
        idea: str,
        deliverables_a: Dict[str, Any],
        deliverables_b: Dict[str, Any],
        mode_a_name: str = "Mode A",
        mode_b_name: str = "Mode B"
    ) -> PairwiseComparison:
        """Pairwise blinded evaluation between two run deliverables."""
        score_a = await self.score_deliverables(deliverables_a, idea)
        score_b = await self.score_deliverables(deliverables_b, idea)

        diff = score_a.composite_10 - score_b.composite_10
        if abs(diff) < 0.2:
            return PairwiseComparison(winner="TIE", margin="slight", key_reasons=["Scores within 0.2 margin"])
        elif diff > 0:
            margin = "decisive" if diff > 1.0 else ("clear" if diff > 0.5 else "slight")
            return PairwiseComparison(winner="A", margin=margin, key_reasons=[f"{mode_a_name} scored higher overall ({score_a.composite_10} vs {score_b.composite_10})"])
        else:
            margin = "decisive" if abs(diff) > 1.0 else ("clear" if abs(diff) > 0.5 else "slight")
            return PairwiseComparison(winner="B", margin=margin, key_reasons=[f"{mode_b_name} scored higher overall ({score_b.composite_10} vs {score_a.composite_10})"])
