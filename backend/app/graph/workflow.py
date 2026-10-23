import copy
import logging
from typing import Dict, Any, List, Optional, Callable, Awaitable
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from backend.app.models.state import RunState
from backend.app.models.schemas import MarketAnalystOutput, ProductManagerOutput, TechArchitectOutput, PitchWriterOutput, CEOCriticReview
from backend.app.agents.market_analyst import MarketAnalystAgent
from backend.app.agents.product_manager import ProductManagerAgent
from backend.app.agents.tech_architect import TechArchitectAgent
from backend.app.agents.pitch_writer import PitchWriterAgent
from backend.app.agents.ceo_critic import CEOCriticAgent
from backend.app.graph.debate import DebateEngine
from backend.app.core.config import settings

logger = logging.getLogger(__name__)

# Type for optional real-time event dispatcher callback
EventCallback = Callable[[Dict[str, Any]], Awaitable[None]]


class CoFounderWorkflow:
    """Multi-Agent LangGraph Workflow Orchestrator (ARCHITECTURE.md §2).
    
    Coordinates sequential execution with CEO quality review gates,
    rejection loops (max 2 retries), peer debate protocol, and final pitch deck generation.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model_default: Optional[str] = None,
        model_critic: Optional[str] = None,
        fallback_models: Optional[List[str]] = None,
        event_callback: Optional[EventCallback] = None,
        checkpointer: Optional[Any] = None
    ):
        self.provider = provider or settings.LLM_PROVIDER
        self.model_default = model_default or settings.MODEL_DEFAULT
        if model_critic:
            self.model_critic = model_critic
        elif self.provider == "ollama" or self.model_default.startswith("ollama:") or (":" in self.model_default and "/" not in self.model_default):
            self.model_critic = self.model_default
        else:
            self.model_critic = settings.MODEL_CRITIC
        self.fallback_models = fallback_models
        self.event_callback = event_callback
        self.checkpointer = checkpointer or MemorySaver()

        async def _on_model_switch(previous_model: str, new_model: str, reason: str):
            await self._emit_event(
                "model_switched",
                previous_model=previous_model,
                new_model=new_model,
                reason=reason
            )

        agent_kwargs = {
            "fallback_models": self.fallback_models,
            "on_switch_callback": _on_model_switch if self.event_callback else None
        }

        # Initialize agents
        self.market_agent = MarketAnalystAgent(model=self.model_default, provider=self.provider, **agent_kwargs)
        self.pm_agent = ProductManagerAgent(model=self.model_default, provider=self.provider, **agent_kwargs)
        self.architect_agent = TechArchitectAgent(model=self.model_default, provider=self.provider, **agent_kwargs)
        self.pitch_agent = PitchWriterAgent(model=self.model_default, provider=self.provider, **agent_kwargs)
        self.critic_agent = CEOCriticAgent(model=self.model_critic, provider=self.provider, **agent_kwargs)
        self.debate_engine = DebateEngine(provider=self.provider, model=self.model_default, **agent_kwargs)

        # Build compiled graph
        self.graph = self._build_graph()

    async def _emit_event(self, event_type: str, **kwargs) -> None:
        """Helper to emit real-time event if subscriber callback is registered."""
        if self.event_callback:
            try:
                event = {"type": event_type, **kwargs}
                await self.event_callback(event)
            except Exception as e:
                logger.warning(f"Failed to emit workflow event '{event_type}': {e}")

    # ==========================================================================
    # Graph Nodes
    # ==========================================================================

    async def intake_node(self, state: RunState) -> Dict[str, Any]:
        """Validate input and initialize state structures."""
        await self._emit_event("run_started", run_id=state["run_id"], idea=state["idea"])
        return {
            "status": "running",
            "scores": state.get("scores") or {"market": [], "prd": [], "architecture": [], "pitch": []},
            "retries": state.get("retries") or {"market": 0, "prd": 0, "architecture": 0, "pitch": 0},
            "token_usage": state.get("token_usage") or {"total": 0, "prompt": 0, "completion": 0},
            "debate_log": state.get("debate_log") or [],
            "debate_round": 0
        }

    async def market_analyst_node(self, state: RunState) -> Dict[str, Any]:
        """Execute Market Analyst agent."""
        await self._emit_event("agent_started", agent="market_analyst", run_id=state["run_id"])
        output, meta = await self.market_agent.run(state["idea"])
        
        # Accumulate tokens
        token_usage = copy.deepcopy(state.get("token_usage", {}))
        token_usage["total"] = token_usage.get("total", 0) + meta.get("tokens", 0)

        await self._emit_event("agent_completed", agent="market_analyst", output=output.model_dump())
        return {
            "market": output.model_dump(),
            "token_usage": token_usage,
            "current_agent": "market_analyst"
        }

    async def review_market_node(self, state: RunState) -> Dict[str, Any]:
        """CEO / Critic review of Market deliverable."""
        version = len(state.get("scores", {}).get("market", [])) + 1
        review, meta = await self.critic_agent.review(
            target_agent="market",
            deliverable_content=state["market"],
            version=version
        )
        
        scores = copy.deepcopy(state.get("scores", {}))
        scores.setdefault("market", []).append(review.score)

        await self._emit_event(
            "score_posted",
            target="market",
            score=review.score,
            pass_=review.pass_,
            required_changes=review.required_changes
        )
        return {
            "scores": scores,
            "_last_review": review.model_dump()
        }

    async def product_manager_node(self, state: RunState) -> Dict[str, Any]:
        """Execute Product Manager agent."""
        await self._emit_event("agent_started", agent="pm", run_id=state["run_id"])
        output, meta = await self.pm_agent.run(state["idea"], state["market"])

        token_usage = copy.deepcopy(state.get("token_usage", {}))
        token_usage["total"] = token_usage.get("total", 0) + meta.get("tokens", 0)

        await self._emit_event("agent_completed", agent="pm", output=output.model_dump())
        return {
            "prd": output.model_dump(),
            "token_usage": token_usage,
            "current_agent": "pm"
        }

    async def review_pm_node(self, state: RunState) -> Dict[str, Any]:
        """CEO / Critic review of PRD deliverable."""
        version = len(state.get("scores", {}).get("prd", [])) + 1
        review, meta = await self.critic_agent.review(
            target_agent="prd",
            deliverable_content=state["prd"],
            version=version,
            prior_context={"market": state["market"]}
        )

        scores = copy.deepcopy(state.get("scores", {}))
        scores.setdefault("prd", []).append(review.score)

        await self._emit_event(
            "score_posted",
            target="prd",
            score=review.score,
            pass_=review.pass_,
            required_changes=review.required_changes
        )
        return {
            "scores": scores,
            "_last_review": review.model_dump()
        }

    async def tech_architect_node(self, state: RunState) -> Dict[str, Any]:
        """Execute Tech Architect agent."""
        await self._emit_event("agent_started", agent="architect", run_id=state["run_id"])
        output, meta = await self.architect_agent.run(state["idea"], state["market"], state["prd"])

        token_usage = copy.deepcopy(state.get("token_usage", {}))
        token_usage["total"] = token_usage.get("total", 0) + meta.get("tokens", 0)

        await self._emit_event("agent_completed", agent="architect", output=output.model_dump())
        return {
            "architecture": output.model_dump(),
            "token_usage": token_usage,
            "current_agent": "architect"
        }

    async def review_architect_node(self, state: RunState) -> Dict[str, Any]:
        """CEO / Critic review of Architecture deliverable."""
        version = len(state.get("scores", {}).get("architecture", [])) + 1
        review, meta = await self.critic_agent.review(
            target_agent="architecture",
            deliverable_content=state["architecture"],
            version=version,
            prior_context={"market": state["market"], "prd": state["prd"]}
        )

        scores = copy.deepcopy(state.get("scores", {}))
        scores.setdefault("architecture", []).append(review.score)

        await self._emit_event(
            "score_posted",
            target="architecture",
            score=review.score,
            pass_=review.pass_,
            required_changes=review.required_changes
        )
        return {
            "scores": scores,
            "_last_review": review.model_dump()
        }

    async def debate_round_node(self, state: RunState) -> Dict[str, Any]:
        """Execute one debate round between Analyst, PM, and Architect."""
        current_round = state.get("debate_round", 0) + 1
        threshold = state.get("options", {}).get("score_threshold", settings.SCORE_THRESHOLD)

        await self._emit_event("debate_started", round=current_round, run_id=state["run_id"])

        messages, updated_market, updated_prd, updated_arch, is_resolved = await self.debate_engine.run_round(
            current_round=current_round,
            market=state["market"],
            prd=state["prd"],
            architecture=state["architecture"],
            score_threshold=threshold
        )

        for msg in messages:
            await self._emit_event(
                "debate_message",
                round=msg["round"],
                from_=msg["from_agent"],
                to=msg["to_agent"],
                content=msg["content"]
            )

        debate_log = list(state.get("debate_log", [])) + messages

        return {
            "market": updated_market,
            "prd": updated_prd,
            "architecture": updated_arch,
            "debate_log": debate_log,
            "debate_round": current_round,
            "_debate_resolved": is_resolved
        }

    async def pitch_writer_node(self, state: RunState) -> Dict[str, Any]:
        """Execute Pitch Writer agent."""
        await self._emit_event("agent_started", agent="pitch_writer", run_id=state["run_id"])
        output, meta = await self.pitch_agent.run(
            idea=state["idea"],
            market=state["market"],
            prd=state["prd"],
            architecture=state["architecture"]
        )

        token_usage = copy.deepcopy(state.get("token_usage", {}))
        token_usage["total"] = token_usage.get("total", 0) + meta.get("tokens", 0)

        await self._emit_event("agent_completed", agent="pitch_writer", output=output.model_dump())
        return {
            "pitch": output.model_dump(),
            "token_usage": token_usage,
            "current_agent": "pitch_writer"
        }

    async def review_pitch_node(self, state: RunState) -> Dict[str, Any]:
        """CEO / Critic review of Pitch Deck."""
        version = len(state.get("scores", {}).get("pitch", [])) + 1
        review, meta = await self.critic_agent.review(
            target_agent="pitch",
            deliverable_content=state["pitch"],
            version=version
        )

        scores = copy.deepcopy(state.get("scores", {}))
        scores.setdefault("pitch", []).append(review.score)

        await self._emit_event(
            "score_posted",
            target="pitch",
            score=review.score,
            pass_=review.pass_,
            required_changes=review.required_changes
        )
        return {
            "scores": scores,
            "_last_review": review.model_dump()
        }

    async def finalize_node(self, state: RunState) -> Dict[str, Any]:
        """Finalize workflow and mark completion status."""
        final_status = "completed"
        # If any agent was accepted after exhausting retries without passing threshold
        retries = state.get("retries", {})
        if any(r >= settings.MAX_RETRIES_PER_AGENT for r in retries.values()):
            final_status = "needs_review"

        await self._emit_event("run_completed", run_id=state["run_id"], status=final_status)
        return {"status": final_status}

    # ==========================================================================
    # Conditional Edge Routers (AGENTS.md & ARCHITECTURE.md §2)
    # ==========================================================================

    def should_retry_market(self, state: RunState) -> str:
        """Route Market Analyst after CEO review."""
        scores = state.get("scores", {}).get("market", [])
        score = scores[-1] if scores else state.get("_last_review", {}).get("score", 0.0)
        retries = state.get("retries", {}).get("market", 0)
        threshold = state.get("options", {}).get("score_threshold", settings.SCORE_THRESHOLD)

        if score >= threshold:
            return "product_manager"
        elif retries < settings.MAX_RETRIES_PER_AGENT:
            state.setdefault("retries", {})["market"] = retries + 1
            return "market_analyst"
        else:
            # AGENTS.md Failure Handling: accept best version, mark needs_review
            return "product_manager"

    def should_retry_pm(self, state: RunState) -> str:
        """Route Product Manager after CEO review."""
        scores = state.get("scores", {}).get("prd", [])
        score = scores[-1] if scores else state.get("_last_review", {}).get("score", 0.0)
        retries = state.get("retries", {}).get("prd", 0)
        threshold = state.get("options", {}).get("score_threshold", settings.SCORE_THRESHOLD)

        if score >= threshold:
            return "tech_architect"
        elif retries < settings.MAX_RETRIES_PER_AGENT:
            state.setdefault("retries", {})["prd"] = retries + 1
            return "product_manager"
        else:
            return "tech_architect"

    def should_retry_architect(self, state: RunState) -> str:
        """Route Tech Architect after CEO review."""
        scores = state.get("scores", {}).get("architecture", [])
        score = scores[-1] if scores else state.get("_last_review", {}).get("score", 0.0)
        retries = state.get("retries", {}).get("architecture", 0)
        threshold = state.get("options", {}).get("score_threshold", settings.SCORE_THRESHOLD)

        max_rounds = state.get("options", {}).get("debate_rounds", settings.DEBATE_MAX_ROUNDS)

        if score >= threshold:
            if max_rounds <= 0:
                return "pitch_writer"
            return "debate_round"
        elif retries < settings.MAX_RETRIES_PER_AGENT:
            state.setdefault("retries", {})["architecture"] = retries + 1
            return "tech_architect"
        else:
            if max_rounds <= 0:
                return "pitch_writer"
            return "debate_round"


    def should_continue_debate(self, state: RunState) -> str:
        """Route Debate Round (max rounds or resolved)."""
        current_round = state.get("debate_round", 0)
        max_rounds = state.get("options", {}).get("debate_rounds", settings.DEBATE_MAX_ROUNDS)
        is_resolved = state.get("_debate_resolved", False)

        if is_resolved or current_round >= max_rounds:
            return "pitch_writer"
        return "debate_round"

    def should_retry_pitch(self, state: RunState) -> str:
        """Route Pitch Writer after CEO final review."""
        scores = state.get("scores", {}).get("pitch", [])
        score = scores[-1] if scores else state.get("_last_review", {}).get("score", 0.0)
        retries = state.get("retries", {}).get("pitch", 0)
        threshold = state.get("options", {}).get("score_threshold", settings.SCORE_THRESHOLD)

        if score >= threshold or retries >= settings.MAX_RETRIES_PER_AGENT:
            return "finalize"
        state.setdefault("retries", {})["pitch"] = retries + 1
        return "pitch_writer"

    # ==========================================================================
    # Graph Construction
    # ==========================================================================

    def _build_graph(self):
        """Construct and compile the LangGraph workflow."""
        builder = StateGraph(RunState)

        # 1. Register nodes
        builder.add_node("intake", self.intake_node)
        builder.add_node("market_analyst", self.market_analyst_node)
        builder.add_node("review_market", self.review_market_node)
        builder.add_node("product_manager", self.product_manager_node)
        builder.add_node("review_pm", self.review_pm_node)
        builder.add_node("tech_architect", self.tech_architect_node)
        builder.add_node("review_architect", self.review_architect_node)
        builder.add_node("debate_round", self.debate_round_node)
        builder.add_node("pitch_writer", self.pitch_writer_node)
        builder.add_node("review_pitch", self.review_pitch_node)
        builder.add_node("finalize", self.finalize_node)

        # 2. Add edges
        builder.add_edge(START, "intake")
        builder.add_edge("intake", "market_analyst")
        builder.add_edge("market_analyst", "review_market")

        builder.add_conditional_edges(
            "review_market",
            self.should_retry_market,
            {
                "product_manager": "product_manager",
                "market_analyst": "market_analyst"
            }
        )

        builder.add_edge("product_manager", "review_pm")
        builder.add_conditional_edges(
            "review_pm",
            self.should_retry_pm,
            {
                "tech_architect": "tech_architect",
                "product_manager": "product_manager"
            }
        )

        builder.add_edge("tech_architect", "review_architect")
        builder.add_conditional_edges(
            "review_architect",
            self.should_retry_architect,
            {
                "debate_round": "debate_round",
                "pitch_writer": "pitch_writer",
                "tech_architect": "tech_architect"
            }
        )

        builder.add_conditional_edges(
            "debate_round",
            self.should_continue_debate,
            {
                "pitch_writer": "pitch_writer",
                "debate_round": "debate_round"
            }
        )

        builder.add_edge("pitch_writer", "review_pitch")
        builder.add_conditional_edges(
            "review_pitch",
            self.should_retry_pitch,
            {
                "finalize": "finalize",
                "pitch_writer": "pitch_writer"
            }
        )

        builder.add_edge("finalize", END)

        return builder.compile(checkpointer=self.checkpointer)
