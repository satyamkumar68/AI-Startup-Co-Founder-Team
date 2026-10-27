import copy
import logging
import time
from typing import Dict, Any, List, Optional, Callable, Awaitable, Literal
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langgraph.types import interrupt

from backend.app.models.state import RunState
from backend.app.models.schemas import MarketAnalystOutput, ProductManagerOutput, TechArchitectOutput, PitchWriterOutput, CEOCriticReview
from backend.app.agents.market_analyst import MarketAnalystAgent
from backend.app.agents.product_manager import ProductManagerAgent
from backend.app.agents.tech_architect import TechArchitectAgent
from backend.app.agents.pitch_writer import PitchWriterAgent
from backend.app.agents.ceo_critic import CEOCriticAgent
from backend.app.agents.single_agent import SingleAgent
from backend.app.graph.debate import DebateEngine
from backend.app.graph.fact_check import FactCheckEngine
from backend.app.core.config import settings
from backend.app.core.security import sanitize_idea_input

logger = logging.getLogger(__name__)

# Type for optional real-time event dispatcher callback
EventCallback = Callable[[Dict[str, Any]], Awaitable[None]]


class CoFounderWorkflow:
    """Multi-Agent LangGraph Workflow Orchestrator (ARCHITECTURE.md §2).
    
    Coordinates sequential execution with CEO quality review gates,
    rejection loops (max 2 retries), peer debate protocol, and final pitch deck generation.
    Supports single_agent, multi_no_debate, and multi_debate run modes for ablation studies.
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        model_default: Optional[str] = None,
        model_critic: Optional[str] = None,
        fallback_models: Optional[List[str]] = None,
        event_callback: Optional[EventCallback] = None,
        checkpointer: Optional[Any] = None,
        mode: Optional[Literal["single_agent", "multi_no_debate", "multi_debate"]] = None
    ):
        self.provider = provider or settings.LLM_PROVIDER
        self.model_default = model_default or settings.MODEL_DEFAULT
        self.mode = mode or settings.MODE
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
        self.single_agent = SingleAgent(model=self.model_default, provider=self.provider, **agent_kwargs)
        self.fact_check_engine = FactCheckEngine()

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

    def _accumulate_telemetry(self, state: RunState, meta: Dict[str, Any]) -> Dict[str, Any]:
        """Helper to accumulate execution metrics (tokens, cost, repairs, fallbacks)."""
        telemetry = copy.deepcopy(state.get("telemetry") or {})
        tokens = telemetry.setdefault("tokens", {"prompt": 0, "completion": 0, "total": 0})
        tokens["total"] = tokens.get("total", 0) + meta.get("tokens", 0)
        tokens["prompt"] = tokens.get("prompt", 0) + meta.get("prompt_tokens", 0)
        tokens["completion"] = tokens.get("completion", 0) + meta.get("completion_tokens", 0)
        telemetry["cost_usd"] = round(telemetry.get("cost_usd", 0.0) + meta.get("cost_usd", 0.0), 4)
        telemetry["schema_repairs"] = telemetry.get("schema_repairs", 0) + meta.get("schema_repairs", 0)
        telemetry["fallback_count"] = max(telemetry.get("fallback_count", 0), meta.get("fallback_count", 0))
        return telemetry

    # ==========================================================================
    # Graph Nodes
    # ==========================================================================

    def _is_budget_exceeded(self, state: RunState) -> bool:
        """Check if total tokens or USD cost exceed configured budget caps."""
        options = state.get("options") or {}
        max_tokens = options.get("max_tokens", settings.MAX_TOKENS_PER_RUN)
        max_budget = options.get("max_budget_usd", settings.MAX_BUDGET_USD_PER_RUN)

        telemetry = state.get("telemetry") or {}
        total_tokens = telemetry.get("tokens", {}).get("total", 0) or state.get("token_usage", {}).get("total", 0)
        total_cost = telemetry.get("cost_usd", 0.0)

        if total_tokens >= max_tokens or total_cost >= max_budget:
            logger.warning(
                f"Budget cap triggered: tokens={total_tokens}/{max_tokens}, "
                f"cost=${total_cost:.4f}/${max_budget:.2f}"
            )
            return True
        return False

    async def intake_node(self, state: RunState) -> Dict[str, Any]:
        """Validate input, sanitize prompt injection attempts, and initialize state structures."""
        raw_idea = state.get("idea", "")
        clean_idea, is_injection, detected_patterns = sanitize_idea_input(raw_idea)

        await self._emit_event("run_started", run_id=state["run_id"], idea=clean_idea)
        
        errors = list(state.get("errors") or [])
        if is_injection:
            errors.append(f"Prompt injection pattern detected and neutralized: {detected_patterns}")
            await self._emit_event("security_warning", detected=detected_patterns)

        run_mode = state.get("mode") or state.get("options", {}).get("mode") or self.mode
        telemetry = state.get("telemetry") or {
            "start_time": time.time(),
            "tokens": {"prompt": 0, "completion": 0, "total": 0},
            "cost_usd": 0.0,
            "latency_sec": 0.0,
            "retries": 0,
            "schema_repairs": 0,
            "fallback_count": 0
        }
        if "start_time" not in telemetry:
            telemetry["start_time"] = time.time()

        return {
            "idea": clean_idea,
            "status": "running",
            "mode": run_mode,
            "telemetry": telemetry,
            "errors": errors,
            "scores": state.get("scores") or {"market": [], "prd": [], "architecture": [], "pitch": []},
            "retries": state.get("retries") or {"market": 0, "prd": 0, "architecture": 0, "pitch": 0},
            "token_usage": state.get("token_usage") or {"total": 0, "prompt": 0, "completion": 0},
            "debate_log": state.get("debate_log") or [],
            "debate_round": 0
        }

    async def single_agent_node(self, state: RunState) -> Dict[str, Any]:
        """Execute Single Agent baseline generating all 4 deliverables in one pass."""
        await self._emit_event("agent_started", agent="single_agent", run_id=state["run_id"])
        deliverables, meta = await self.single_agent.run(state["idea"])

        token_usage = copy.deepcopy(state.get("token_usage", {}))
        token_usage["total"] = token_usage.get("total", 0) + meta.get("tokens", 0)
        token_usage["prompt"] = token_usage.get("prompt", 0) + meta.get("prompt_tokens", 0)
        token_usage["completion"] = token_usage.get("completion", 0) + meta.get("completion_tokens", 0)

        telemetry = self._accumulate_telemetry(state, meta)

        scores = {
            "market": [7.5],
            "prd": [7.5],
            "architecture": [7.5],
            "pitch": [7.5]
        }

        await self._emit_event("agent_completed", agent="single_agent", output={"status": "completed"})
        return {
            "market": deliverables.market.model_dump(),
            "prd": deliverables.prd.model_dump(),
            "architecture": deliverables.architecture.model_dump(),
            "pitch": deliverables.pitch.model_dump(),
            "token_usage": token_usage,
            "telemetry": telemetry,
            "scores": scores,
            "current_agent": "single_agent"
        }

    async def market_analyst_node(self, state: RunState) -> Dict[str, Any]:
        """Execute Market Analyst agent."""
        await self._emit_event("agent_started", agent="market_analyst", run_id=state["run_id"])
        output, meta = await self.market_agent.run(state["idea"])
        
        # Accumulate tokens
        token_usage = copy.deepcopy(state.get("token_usage", {}))
        token_usage["total"] = token_usage.get("total", 0) + meta.get("tokens", 0)
        telemetry = self._accumulate_telemetry(state, meta)

        await self._emit_event("agent_completed", agent="market_analyst", output=output.model_dump())
        return {
            "market": output.model_dump(),
            "token_usage": token_usage,
            "telemetry": telemetry,
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
        telemetry = self._accumulate_telemetry(state, meta)

        await self._emit_event("agent_completed", agent="pm", output=output.model_dump())
        return {
            "prd": output.model_dump(),
            "token_usage": token_usage,
            "telemetry": telemetry,
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

    async def human_review_node(self, state: RunState) -> Dict[str, Any]:
        """Optional Human-in-the-Loop review interrupt before technical architecture."""
        enable_human = state.get("options", {}).get("enable_human_review", False)
        if not enable_human:
            return {}

        await self._emit_event(
            "awaiting_human_review",
            deliverable="prd",
            content=state.get("prd")
        )

        user_feedback = interrupt({
            "type": "human_review",
            "target": "prd",
            "content": state.get("prd"),
            "message": "Review and approve or edit the PRD deliverable before technical architecture."
        })

        updates: Dict[str, Any] = {}
        if isinstance(user_feedback, dict):
            if user_feedback.get("edited_prd"):
                updates["prd"] = user_feedback["edited_prd"]
            if user_feedback.get("feedback"):
                errors = list(state.get("errors") or [])
                errors.append(f"Human reviewer feedback: {user_feedback['feedback']}")
                updates["errors"] = errors

        await self._emit_event("human_review_completed", feedback=user_feedback)
        return updates

    async def tech_architect_node(self, state: RunState) -> Dict[str, Any]:
        """Execute Tech Architect agent."""
        await self._emit_event("agent_started", agent="architect", run_id=state["run_id"])
        output, meta = await self.architect_agent.run(state["idea"], state["market"], state["prd"])

        token_usage = copy.deepcopy(state.get("token_usage", {}))
        token_usage["total"] = token_usage.get("total", 0) + meta.get("tokens", 0)
        telemetry = self._accumulate_telemetry(state, meta)

        await self._emit_event("agent_completed", agent="architect", output=output.model_dump())
        return {
            "architecture": output.model_dump(),
            "token_usage": token_usage,
            "telemetry": telemetry,
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
        telemetry = self._accumulate_telemetry(state, meta)

        await self._emit_event("agent_completed", agent="pitch_writer", output=output.model_dump())
        return {
            "pitch": output.model_dump(),
            "token_usage": token_usage,
            "telemetry": telemetry,
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

    async def fact_check_node(self, state: RunState) -> Dict[str, Any]:
        """Execute FactCheck verification node scanning claims and building verification appendix."""
        await self._emit_event("agent_started", agent="fact_check", run_id=state["run_id"])
        verification = self.fact_check_engine.verify(state)
        await self._emit_event(
            "fact_check_completed",
            verified_count=verification.get("verified_count", 0),
            assumption_count=verification.get("assumption_count", 0),
            unverified_count=verification.get("unverified_count", 0),
            flagged_claims=verification.get("flagged_claims", [])
        )
        return {"verification": verification}

    async def finalize_node(self, state: RunState) -> Dict[str, Any]:
        """Finalize workflow and mark completion status."""
        final_status = "completed"
        if state.get("status") == "budget_exceeded":
            final_status = "budget_exceeded"
        else:
            # If any agent was accepted after exhausting retries without passing threshold
            retries = state.get("retries", {})
            if any(r >= settings.MAX_RETRIES_PER_AGENT for r in retries.values()):
                final_status = "needs_review"

        telemetry = copy.deepcopy(state.get("telemetry") or {})
        start_time = telemetry.get("start_time", time.time())
        telemetry["latency_sec"] = round(time.time() - start_time, 2)
        telemetry["retries"] = sum(state.get("retries", {}).values())
        tokens = telemetry.setdefault("tokens", {"prompt": 0, "completion": 0, "total": 0})
        if tokens.get("total", 0) == 0 and state.get("token_usage", {}).get("total", 0) > 0:
            tokens["total"] = state["token_usage"]["total"]

        await self._emit_event("run_completed", run_id=state["run_id"], status=final_status)
        return {"status": final_status, "telemetry": telemetry}

    # ==========================================================================
    # Conditional Edge Routers (AGENTS.md & ARCHITECTURE.md §2)
    # ==========================================================================

    def route_after_intake(self, state: RunState) -> str:
        """Route workflow after intake depending on execution mode."""
        mode = state.get("mode") or self.mode
        if mode == "single_agent":
            return "single_agent"
        return "market_analyst"

    def should_retry_market(self, state: RunState) -> str:
        """Route Market Analyst after CEO review."""
        if self._is_budget_exceeded(state):
            state["status"] = "budget_exceeded"
            return "fact_check"
        mode = state.get("mode") or self.mode
        if mode == "multi_no_debate":
            return "product_manager"
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
        if self._is_budget_exceeded(state):
            state["status"] = "budget_exceeded"
            return "fact_check"

        enable_human = state.get("options", {}).get("enable_human_review", False)
        advance_target = "human_review" if enable_human else "tech_architect"

        mode = state.get("mode") or self.mode
        if mode == "multi_no_debate":
            return advance_target
        scores = state.get("scores", {}).get("prd", [])
        score = scores[-1] if scores else state.get("_last_review", {}).get("score", 0.0)
        retries = state.get("retries", {}).get("prd", 0)
        threshold = state.get("options", {}).get("score_threshold", settings.SCORE_THRESHOLD)

        if score >= threshold:
            return advance_target
        elif retries < settings.MAX_RETRIES_PER_AGENT:
            state.setdefault("retries", {})["prd"] = retries + 1
            return "product_manager"
        else:
            return advance_target

    def should_retry_architect(self, state: RunState) -> str:
        """Route Tech Architect after CEO review."""
        if self._is_budget_exceeded(state):
            state["status"] = "budget_exceeded"
            return "fact_check"
        mode = state.get("mode") or self.mode
        if mode == "multi_no_debate":
            return "pitch_writer"
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
        """Route Debate Round (max rounds, resolved, or budget exceeded)."""
        if self._is_budget_exceeded(state):
            state["status"] = "budget_exceeded"
            return "fact_check"
        current_round = state.get("debate_round", 0)
        max_rounds = state.get("options", {}).get("debate_rounds", settings.DEBATE_MAX_ROUNDS)
        is_resolved = state.get("_debate_resolved", False)

        if is_resolved or current_round >= max_rounds:
            return "pitch_writer"
        return "debate_round"

    def should_retry_pitch(self, state: RunState) -> str:
        """Route Pitch Writer after CEO final review."""
        if self._is_budget_exceeded(state):
            state["status"] = "budget_exceeded"
            return "fact_check"
        mode = state.get("mode") or self.mode
        if mode == "multi_no_debate":
            return "fact_check"
        scores = state.get("scores", {}).get("pitch", [])
        score = scores[-1] if scores else state.get("_last_review", {}).get("score", 0.0)
        retries = state.get("retries", {}).get("pitch", 0)
        threshold = state.get("options", {}).get("score_threshold", settings.SCORE_THRESHOLD)

        if score >= threshold or retries >= settings.MAX_RETRIES_PER_AGENT:
            return "fact_check"
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
        builder.add_node("single_agent", self.single_agent_node)
        builder.add_node("market_analyst", self.market_analyst_node)
        builder.add_node("review_market", self.review_market_node)
        builder.add_node("product_manager", self.product_manager_node)
        builder.add_node("review_pm", self.review_pm_node)
        builder.add_node("human_review", self.human_review_node)
        builder.add_node("tech_architect", self.tech_architect_node)
        builder.add_node("review_architect", self.review_architect_node)
        builder.add_node("debate_round", self.debate_round_node)
        builder.add_node("pitch_writer", self.pitch_writer_node)
        builder.add_node("review_pitch", self.review_pitch_node)
        builder.add_node("fact_check", self.fact_check_node)
        builder.add_node("finalize", self.finalize_node)

        # 2. Add edges
        builder.add_edge(START, "intake")
        builder.add_conditional_edges(
            "intake",
            self.route_after_intake,
            {
                "single_agent": "single_agent",
                "market_analyst": "market_analyst"
            }
        )
        builder.add_edge("single_agent", "fact_check")
        builder.add_edge("market_analyst", "review_market")

        builder.add_conditional_edges(
            "review_market",
            self.should_retry_market,
            {
                "product_manager": "product_manager",
                "market_analyst": "market_analyst",
                "fact_check": "fact_check"
            }
        )

        builder.add_edge("product_manager", "review_pm")
        builder.add_conditional_edges(
            "review_pm",
            self.should_retry_pm,
            {
                "human_review": "human_review",
                "tech_architect": "tech_architect",
                "product_manager": "product_manager",
                "fact_check": "fact_check"
            }
        )
        builder.add_edge("human_review", "tech_architect")

        builder.add_edge("tech_architect", "review_architect")
        builder.add_conditional_edges(
            "review_architect",
            self.should_retry_architect,
            {
                "debate_round": "debate_round",
                "pitch_writer": "pitch_writer",
                "tech_architect": "tech_architect",
                "fact_check": "fact_check"
            }
        )

        builder.add_conditional_edges(
            "debate_round",
            self.should_continue_debate,
            {
                "pitch_writer": "pitch_writer",
                "debate_round": "debate_round",
                "fact_check": "fact_check"
            }
        )

        builder.add_edge("pitch_writer", "review_pitch")
        builder.add_conditional_edges(
            "review_pitch",
            self.should_retry_pitch,
            {
                "fact_check": "fact_check",
                "pitch_writer": "pitch_writer"
            }
        )

        builder.add_edge("fact_check", "finalize")
        builder.add_edge("finalize", END)

        return builder.compile(checkpointer=self.checkpointer)
