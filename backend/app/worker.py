import os
import json
import uuid
import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from backend.app.core.config import settings
from backend.app.db.session import AsyncSessionLocal
from backend.app.models.db import Run, AgentOutput, Score, DebateMessage, Export
from backend.app.models.state import RunState
from backend.app.graph.workflow import CoFounderWorkflow
from backend.app.exporters.manager import ExportManager
from backend.app.api.websocket import ws_manager

logger = logging.getLogger(__name__)

# Registry of active asyncio tasks for cancellation support (FR-12)
ACTIVE_RUN_TASKS: Dict[str, asyncio.Task] = {}
# Registry of active workflows awaiting human review approval
ACTIVE_WORKFLOWS: Dict[str, Dict[str, Any]] = {}


async def _persist_and_broadcast_run_completion(
    run_id: str,
    final_state: RunState,
    options: Dict[str, Any],
    event_broadcaster: Any
) -> None:
    """Helper to persist all final deliverables to DB and broadcast run completion."""
    final_status = final_state.get("status", "completed")

    async with AsyncSessionLocal() as session:
        try:
            run_uuid = uuid.UUID(run_id)

            # Persist Agent Outputs
            for agent_name, key in [
                ("market_analyst", "market"),
                ("pm", "prd"),
                ("architect", "architecture"),
                ("pitch_writer", "pitch"),
                ("fact_check", "fact_check")
            ]:
                data = final_state.get(key)
                if data:
                    out_rec = AgentOutput(
                        run_id=run_uuid,
                        agent=agent_name,
                        version=1,
                        output=data
                    )
                    session.add(out_rec)

            # Persist Scores
            for target, score_vals in final_state.get("scores", {}).items():
                for v_idx, sc in enumerate(score_vals):
                    score_rec = Score(
                        run_id=run_uuid,
                        target_agent=target,
                        version=v_idx + 1,
                        score=sc,
                        passed=sc >= options.get("score_threshold", settings.SCORE_THRESHOLD)
                    )
                    session.add(score_rec)

            # Persist Debate Messages
            for msg in final_state.get("debate_log", []):
                d_rec = DebateMessage(
                    run_id=run_uuid,
                    round=msg.get("round", 1),
                    from_agent=msg.get("from_agent", ""),
                    to_agent=msg.get("to_agent", ""),
                    content=msg.get("content", {})
                )
                session.add(d_rec)

            # Update Run Completion Status
            total_tokens = final_state.get("token_usage", {}).get("total", 0)
            total_cost = (total_tokens / 1000) * 0.005

            up_query = (
                update(Run)
                .where(Run.id == run_uuid)
                .values(
                    status=final_status,
                    total_tokens=total_tokens,
                    total_cost_usd=total_cost,
                    completed_at=datetime.now(timezone.utc)
                )
            )
            await session.execute(up_query)
            await session.commit()
        except Exception as db_err:
            logger.error(f"Error persisting run results to database: {db_err}")

    # Sync memory store fallback
    try:
        from backend.app.api.routes import _RUNS_MEM_STORE
        if run_id in _RUNS_MEM_STORE:
            _RUNS_MEM_STORE[run_id]["status"] = final_status
            _RUNS_MEM_STORE[run_id]["market"] = final_state.get("market")
            _RUNS_MEM_STORE[run_id]["prd"] = final_state.get("prd")
            _RUNS_MEM_STORE[run_id]["architecture"] = final_state.get("architecture")
            _RUNS_MEM_STORE[run_id]["pitch"] = final_state.get("pitch")
            _RUNS_MEM_STORE[run_id]["fact_check"] = final_state.get("fact_check")
            _RUNS_MEM_STORE[run_id]["telemetry"] = final_state.get("telemetry")
            _RUNS_MEM_STORE[run_id]["scores"] = final_state.get("scores", {})
            _RUNS_MEM_STORE[run_id]["debate_messages"] = final_state.get("debate_log", [])
            _RUNS_MEM_STORE[run_id]["total_tokens"] = total_tokens
            _RUNS_MEM_STORE[run_id]["total_cost_usd"] = total_cost
            _RUNS_MEM_STORE[run_id]["completed_at"] = datetime.now(timezone.utc).isoformat()
    except Exception:
        pass

    export_results = {
        fmt: f"/api/v1/runs/{run_id}/export?format={fmt}"
        for fmt in ["pdf", "pptx", "md", "csv"]
    }

    # Broadcast run completed event
    await event_broadcaster({
        "type": "run_completed",
        "status": final_status,
        "exports": export_results
    })


async def resume_run_pipeline(run_id: str, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
    """Resume execution of an interrupted workflow at human review checkpoint."""
    from langgraph.types import Command
    wf_entry = ACTIVE_WORKFLOWS.get(run_id)
    if not wf_entry:
        raise ValueError(f"No active paused workflow found for run_id {run_id}")

    workflow: CoFounderWorkflow = wf_entry["workflow"]
    options: Dict[str, Any] = wf_entry["options"]
    event_broadcaster = wf_entry["event_broadcaster"]

    logger.info(f"Resuming run {run_id} with human reviewer input: {feedback_data}")

    # Update status to running
    async with AsyncSessionLocal() as session:
        try:
            run_uuid = uuid.UUID(run_id)
            await session.execute(update(Run).where(Run.id == run_uuid).values(status="running"))
            await session.commit()
        except Exception:
            pass

    from backend.app.api.routes import _RUNS_MEM_STORE
    if run_id in _RUNS_MEM_STORE:
        _RUNS_MEM_STORE[run_id]["status"] = "running"

    config = {"configurable": {"thread_id": run_id}}
    final_state = await workflow.graph.ainvoke(
        Command(resume=feedback_data),
        config=config
    )

    ACTIVE_WORKFLOWS.pop(run_id, None)
    await _persist_and_broadcast_run_completion(run_id, final_state, options, event_broadcaster)
    return final_state


async def execute_run_pipeline(run_id: str, idea: str, options: Dict[str, Any]) -> None:
    """Execute the full multi-agent pipeline for a run, broadcasting events and persisting outputs."""
    logger.info(f"Starting execution for run {run_id}: '{idea[:40]}...'")

    export_mgr = ExportManager()

    async def event_broadcaster(event: Dict[str, Any]) -> None:
        """Forward pipeline events to connected WebSocket clients and persist intermediate outputs."""
        event["run_id"] = run_id
        event["ts"] = datetime.now(timezone.utc).isoformat()
        await ws_manager.broadcast(run_id, event)

        # Real-time incremental persistence to DB & in-memory store
        ev_type = event.get("type")
        from backend.app.api.routes import _RUNS_MEM_STORE

        if ev_type == "agent_completed":
            agent = event.get("agent")
            output_data = event.get("output")
            key_map = {"market_analyst": "market", "pm": "prd", "architect": "architecture", "pitch_writer": "pitch"}
            state_key = key_map.get(agent)

            if agent == "single_agent" and isinstance(output_data, dict):
                for k in ["market", "prd", "architecture", "pitch"]:
                    if k in output_data and run_id in _RUNS_MEM_STORE:
                        _RUNS_MEM_STORE[run_id][k] = output_data[k]
                try:
                    run_uuid = uuid.UUID(run_id)
                    async with AsyncSessionLocal() as session:
                        for k, aname in [("market", "market_analyst"), ("prd", "pm"), ("architecture", "architect"), ("pitch", "pitch_writer")]:
                            if k in output_data:
                                session.add(AgentOutput(run_id=run_uuid, agent=aname, version=1, output=output_data[k]))
                        await session.commit()
                except Exception as e:
                    logger.debug(f"Incremental single_agent agent_output write: {e}")

            elif state_key and run_id in _RUNS_MEM_STORE:
                _RUNS_MEM_STORE[run_id][state_key] = output_data
                try:
                    run_uuid = uuid.UUID(run_id)
                    async with AsyncSessionLocal() as session:
                        existing = (await session.execute(
                            select(AgentOutput).where(AgentOutput.run_id == run_uuid, AgentOutput.agent == agent)
                        )).scalars().all()
                        rec = AgentOutput(run_id=run_uuid, agent=agent, version=len(existing) + 1, output=output_data)
                        session.add(rec)
                        await session.commit()
                except Exception as e:
                    logger.debug(f"Incremental agent_output write: {e}")

        elif ev_type == "score_posted":
            target = event.get("target")
            score_val = event.get("score")
            if target and score_val is not None and run_id in _RUNS_MEM_STORE:
                _RUNS_MEM_STORE[run_id].setdefault("scores", {}).setdefault(target, []).append(float(score_val))

            try:
                run_uuid = uuid.UUID(run_id)
                async with AsyncSessionLocal() as session:
                    existing_sc = (await session.execute(
                        select(Score).where(Score.run_id == run_uuid, Score.target_agent == target)
                    )).scalars().all()
                    rec = Score(run_id=run_uuid, target_agent=target, version=len(existing_sc) + 1, score=float(score_val), passed=event.get("pass_", True))
                    session.add(rec)
                    await session.commit()
            except Exception as e:
                logger.debug(f"Incremental score write: {e}")

        elif ev_type == "debate_message":
            if run_id in _RUNS_MEM_STORE:
                _RUNS_MEM_STORE[run_id].setdefault("debate_messages", []).append(event)
            try:
                run_uuid = uuid.UUID(run_id)
                async with AsyncSessionLocal() as session:
                    rec = DebateMessage(run_id=run_uuid, round=event.get("round", 1), from_agent=event.get("from_", ""), to_agent=event.get("to", ""), content=event.get("content", {}))
                    session.add(rec)
                    await session.commit()
            except Exception as e:
                logger.debug(f"Incremental debate write: {e}")

    # 1. Update run status to 'running' in database
    async with AsyncSessionLocal() as session:
        try:
            run_uuid = uuid.UUID(run_id)
            query = update(Run).where(Run.id == run_uuid).values(status="running")
            await session.execute(query)
            await session.commit()
        except Exception as e:
            logger.warning(f"Could not update run status in DB: {e}")

    try:
        from backend.app.api.routes import _RUNS_MEM_STORE
        if run_id in _RUNS_MEM_STORE:
            _RUNS_MEM_STORE[run_id]["status"] = "running"
    except Exception:
        pass

    # 2. Build and execute workflow
    provider = (options.get("provider") or settings.LLM_PROVIDER).lower()
    model_override = options.get("model_override") or settings.MODEL_DEFAULT

    if model_override:
        if model_override.startswith("ollama:") or model_override.startswith("ollama/"):
            provider = "ollama"
            model_override = model_override.split(":", 1)[-1].split("/", 1)[-1]
        elif ":" in model_override and "/" not in model_override:
            provider = "ollama"
        elif model_override.startswith("openrouter/"):
            provider = "openrouter"
            model_override = model_override.replace("openrouter/", "", 1)
        elif options.get("provider"):
            provider = options.get("provider").lower()

    fallback_models = options.get("fallback_models")

    workflow = CoFounderWorkflow(
        provider=provider,
        model_default=model_override,
        model_critic=model_override if provider == "ollama" else settings.MODEL_CRITIC,
        fallback_models=fallback_models,
        event_callback=event_broadcaster
    )

    initial_state: RunState = {
        "run_id": run_id,
        "idea": idea,
        "market": None,
        "prd": None,
        "architecture": None,
        "pitch": None,
        "scores": {"market": [], "prd": [], "architecture": [], "pitch": []},
        "debate_log": [],
        "retries": {"market": 0, "prd": 0, "architecture": 0, "pitch": 0},
        "token_usage": {"total": 0, "prompt": 0, "completion": 0},
        "status": "running",
        "options": options,
        "current_agent": None,
        "errors": [],
        "debate_round": 0,
        "user_id": None
    }

    try:
        final_state = await workflow.graph.ainvoke(
            initial_state,
            config={"configurable": {"thread_id": run_id}}
        )

        if final_state.get("__interrupt__"):
            logger.info(f"Run {run_id} paused at human review interrupt.")
            ACTIVE_WORKFLOWS[run_id] = {
                "workflow": workflow,
                "options": options,
                "event_broadcaster": event_broadcaster,
                "state": final_state
            }
            async with AsyncSessionLocal() as session:
                try:
                    run_uuid = uuid.UUID(run_id)
                    await session.execute(update(Run).where(Run.id == run_uuid).values(status="awaiting_approval"))
                    await session.commit()
                except Exception as e:
                    logger.warning(f"Could not update status to awaiting_approval: {e}")

            from backend.app.api.routes import _RUNS_MEM_STORE
            if run_id in _RUNS_MEM_STORE:
                _RUNS_MEM_STORE[run_id]["status"] = "awaiting_approval"
                _RUNS_MEM_STORE[run_id]["prd"] = final_state.get("prd")
                _RUNS_MEM_STORE[run_id]["market"] = final_state.get("market")

            await event_broadcaster({
                "type": "awaiting_human_review",
                "deliverable": "prd",
                "content": final_state.get("prd")
            })
            return

        await _persist_and_broadcast_run_completion(run_id, final_state, options, event_broadcaster)

    except asyncio.CancelledError:
        logger.info(f"Run {run_id} was cancelled by user.")
        async with AsyncSessionLocal() as session:
            try:
                run_uuid = uuid.UUID(run_id)
                await session.execute(
                    update(Run).where(Run.id == run_uuid).values(status="cancelled")
                )
                await session.commit()
            except Exception:
                pass
        await event_broadcaster({"type": "run_failed", "error": "Run was cancelled by user."})
        raise

    except Exception as err:
        logger.error(f"Pipeline execution failed for run {run_id}: {err}", exc_info=True)
        async with AsyncSessionLocal() as session:
            try:
                run_uuid = uuid.UUID(run_id)
                await session.execute(
                    update(Run).where(Run.id == run_uuid).values(status="failed")
                )
                await session.commit()
            except Exception:
                pass
        await event_broadcaster({"type": "run_failed", "error": str(err)})

    finally:
        ACTIVE_RUN_TASKS.pop(run_id, None)


def dispatch_run(run_id: str, idea: str, options: Dict[str, Any]) -> None:
    """Dispatch run execution in background task."""
    task = asyncio.create_task(execute_run_pipeline(run_id, idea, options))
    ACTIVE_RUN_TASKS[run_id] = task


def cancel_run(run_id: str) -> bool:
    """Cancel an ongoing run task (FR-12)."""
    task = ACTIVE_RUN_TASKS.get(run_id)
    if task and not task.done():
        task.cancel()
        return True
    return False


async def start_redis_worker() -> None:
    """Standalone worker loop listening to Redis job queue: queue:runs (ADR-003)."""
    logger.info("Starting Redis background worker loop...")
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        while True:
            # BLPOP waits for items in queue:runs
            item = await r.blpop("queue:runs", timeout=5)
            if item:
                _, payload_str = item
                data = json.loads(payload_str)
                await execute_run_pipeline(
                    run_id=data["run_id"],
                    idea=data["idea"],
                    options=data.get("options", {})
                )
    except asyncio.CancelledError:
        pass
    except Exception as e:
        logger.warning(f"Redis worker loop exited: {e}")


if __name__ == "__main__":
    # When run directly, start worker process
    asyncio.run(start_redis_worker())
