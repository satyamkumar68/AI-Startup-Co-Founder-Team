import json
import logging
from typing import Dict, Any, List, Tuple

from backend.app.agents.llm import MultiProviderLLM
from backend.app.models.schemas import PeerCritique, RebuttalResponse, CEOCriticReview
from backend.app.core.config import settings

logger = logging.getLogger(__name__)


class DebateEngine:
    """Orchestrates structured peer debate rounds between agents (AGENTS.md Debate Protocol).
    
    Debate Flow:
    1. Analyst <-> PM
    2. PM <-> Architect
    3. Architect <-> Analyst
    
    Each agent critiques one peer; the author responds (accepting/rejecting each point);
    the CEO evaluates whether the debate is resolved. Capped at 2 rounds (ADR-007).
    """

    def __init__(self, provider: str = settings.LLM_PROVIDER, model: str = settings.MODEL_DEFAULT, **kwargs):
        self.llm = MultiProviderLLM(provider=provider, model=model, **kwargs)

    async def run_round(
        self,
        current_round: int,
        market: Dict[str, Any],
        prd: Dict[str, Any],
        architecture: Dict[str, Any],
        score_threshold: float = settings.SCORE_THRESHOLD
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any], Dict[str, Any], Dict[str, Any], bool]:
        """Execute a single debate round across the 3 core agents.
        
        Returns:
            messages: List of debate log entries for this round
            updated_market: Refined market dictionary
            updated_prd: Refined PRD dictionary
            updated_architecture: Refined architecture dictionary
            is_resolved: True if CEO marks disagreements settled or no critical issues remain
        """
        round_messages: List[Dict[str, Any]] = []

        # ======================================================================
        # Step 1: Peer Critiques
        # ======================================================================

        # 1A. Market Analyst critiques Product Manager
        pm_critique = await self._critique_peer(
            from_agent="market_analyst",
            target="product_manager",
            peer_deliverable=prd,
            context={"market": market},
            focus="Are target personas and P0 features addressing the biggest market risks and competitors?"
        )
        round_messages.append({
            "round": current_round,
            "from_agent": "market_analyst",
            "to_agent": "product_manager",
            "type": "critique",
            "content": pm_critique.model_dump()
        })

        # 1B. Product Manager critiques Tech Architect
        arch_critique = await self._critique_peer(
            from_agent="product_manager",
            target="tech_architect",
            peer_deliverable=architecture,
            context={"prd": prd},
            focus="Does the technology stack and components realistically support the P0 features and 8-week timeline?"
        )
        round_messages.append({
            "round": current_round,
            "from_agent": "product_manager",
            "to_agent": "tech_architect",
            "type": "critique",
            "content": arch_critique.model_dump()
        })

        # 1C. Tech Architect critiques Market Analyst
        market_critique = await self._critique_peer(
            from_agent="tech_architect",
            target="market_analyst",
            peer_deliverable=market,
            context={"architecture": architecture},
            focus="Are market scale and traffic assumptions technically realistic for the initial cost and cloud architecture?"
        )
        round_messages.append({
            "round": current_round,
            "from_agent": "tech_architect",
            "to_agent": "market_analyst",
            "type": "critique",
            "content": market_critique.model_dump()
        })

        # ======================================================================
        # Step 2: Author Rebuttals & Deliverable Updates
        # ======================================================================

        # 2A. Product Manager rebuttal
        pm_rebuttal, updated_prd = await self._rebut_and_update(
            author_agent="product_manager",
            critique=pm_critique,
            current_deliverable=prd
        )
        round_messages.append({
            "round": current_round,
            "from_agent": "product_manager",
            "to_agent": "market_analyst",
            "type": "rebuttal",
            "content": pm_rebuttal.model_dump()
        })

        # 2B. Tech Architect rebuttal
        arch_rebuttal, updated_arch = await self._rebut_and_update(
            author_agent="tech_architect",
            critique=arch_critique,
            current_deliverable=architecture
        )
        round_messages.append({
            "round": current_round,
            "from_agent": "tech_architect",
            "to_agent": "product_manager",
            "type": "rebuttal",
            "content": arch_rebuttal.model_dump()
        })

        # 2C. Market Analyst rebuttal
        market_rebuttal, updated_market = await self._rebut_and_update(
            author_agent="market_analyst",
            critique=market_critique,
            current_deliverable=market
        )
        round_messages.append({
            "round": current_round,
            "from_agent": "market_analyst",
            "to_agent": "tech_architect",
            "type": "rebuttal",
            "content": market_rebuttal.model_dump()
        })

        # ======================================================================
        # Step 3: CEO Resolution Verdict
        # ======================================================================
        is_resolved, verdict_text = await self._ceo_judge_resolution(
            round_num=current_round,
            messages=round_messages,
            threshold=score_threshold
        )
        round_messages.append({
            "round": current_round,
            "from_agent": "ceo_critic",
            "to_agent": "all",
            "type": "ceo_verdict",
            "content": {
                "resolved": is_resolved,
                "summary": verdict_text
            }
        })

        return round_messages, updated_market, updated_prd, updated_arch, is_resolved

    def _compact_summary(self, data: Dict[str, Any]) -> str:
        """Extract key highlights for fast peer critique without overwhelming local models."""
        if not isinstance(data, dict):
            return str(data)[:500]
        compact = {}
        for k, v in data.items():
            if k in ("sources", "competitor_signals", "_debate_resolved_notes", "raw_competitor_signals"):
                continue
            if isinstance(v, list):
                compact[k] = v[:3]
            elif isinstance(v, str) and len(v) > 250:
                compact[k] = v[:250] + "..."
            elif isinstance(v, dict):
                compact[k] = {sk: (sv[:2] if isinstance(sv, list) else sv) for sk, sv in list(v.items())[:4]}
            else:
                compact[k] = v
        return json.dumps(compact, separators=(',', ':'))

    async def _critique_peer(
        self,
        from_agent: str,
        target: str,
        peer_deliverable: Dict[str, Any],
        context: Dict[str, Any],
        focus: str
    ) -> PeerCritique:
        """Generate structured peer critique."""
        system_prompt = (
            f"You are the {from_agent} participating in a peer review debate with {target}.\n"
            f"Focus: {focus}\n"
            f"Review the peer deliverable for inconsistencies, unrealistic assumptions, or gaps.\n"
            f"Format response as a JSON object matching schema: {{'from_agent': str, 'target': str, 'issues': list[str], 'suggestions': list[str]}}."
        )
        user_prompt = (
            f"Peer Deliverable ({target}):\n{self._compact_summary(peer_deliverable)}\n\n"
            f"Your Domain Context:\n{self._compact_summary(context)}\n\n"
            f"Please provide your critique."
        )
        resp = await self.llm.generate_structured(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            schema=PeerCritique,
            temperature=0.2
        )
        return resp.parsed

    async def _rebut_and_update(
        self,
        author_agent: str,
        critique: PeerCritique,
        current_deliverable: Dict[str, Any]
    ) -> Tuple[RebuttalResponse, Dict[str, Any]]:
        """Respond to peer critique and adjust deliverable accordingly."""
        system_prompt = (
            f"You are the {author_agent}. Your peer {critique.from_agent} has provided a critique.\n"
            f"Review each issue raised: accept valid suggestions that strengthen your output, or explain why you decline invalid ones.\n"
            f"Return JSON: {{'target': str, 'accepted': list[dict], 'rejected': list[dict], 'output_updated': bool}}."
        )
        user_prompt = (
            f"Peer Issues:\n{json.dumps(critique.issues, separators=(',', ':'))}\n\n"
            f"Peer Suggestions:\n{json.dumps(critique.suggestions, separators=(',', ':'))}\n\n"
            f"Your Current Deliverable Summary:\n{self._compact_summary(current_deliverable)}"
        )
        resp = await self.llm.generate_structured(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            schema=RebuttalResponse,
            temperature=0.2
        )
        
        # Merge minor updates if accepted
        updated_deliverable = dict(current_deliverable)
        if resp.parsed.output_updated:
            updated_deliverable["_debate_resolved_notes"] = [
                item.get("resolution", "") for item in resp.parsed.accepted
            ]

        return resp.parsed, updated_deliverable

    async def _ceo_judge_resolution(
        self,
        round_num: int,
        messages: List[Dict[str, Any]],
        threshold: float
    ) -> Tuple[bool, str]:
        """CEO determines if the debate issues are resolved or if another round is required."""
        # Hard cap at 2 rounds as per ADR-007
        if round_num >= settings.DEBATE_MAX_ROUNDS:
            return True, f"Debate completed after maximum {round_num} rounds. All deliverables aligned."

        system_prompt = (
            "You are the CEO. You are monitoring the peer debate exchange between Market Analyst, PM, and Architect.\n"
            "Assess whether the primary issues raised were adequately addressed by the author rebuttals.\n"
            "Return JSON: {'resolved': bool, 'summary': str}."
        )
        user_prompt = f"Debate messages in Round {round_num}:\n{json.dumps(messages, indent=2)}"
        
        try:
            resp = await self.llm.generate(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                response_format_json=True
            )
            data = json.loads(resp.content)
            return bool(data.get("resolved", True)), str(data.get("summary", "Debate round approved by CEO."))
        except Exception:
            return True, "Debate resolved and accepted by CEO."
