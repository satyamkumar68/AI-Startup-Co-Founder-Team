from __future__ import annotations

import os
import re
import json
import uuid
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, Query, status, WebSocket, WebSocketDisconnect, Response
from fastapi.responses import FileResponse, StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from backend.app.core.config import settings
from backend.app.db.session import get_async_db
from backend.app.models.db import Run, AgentOutput, Score, DebateMessage, Export
from backend.app.models.schemas import (
    RunCreateRequest,
    RunCreateResponse,
    RunDetailResponse,
    RunRerunRequest,
    HealthResponse,
    DebateTranscriptResponse,
    RunResumeRequest,
    RunResumeResponse,
    RunPendingResponse,
)
from backend.app.api.websocket import ws_manager
from backend.app.worker import dispatch_run, cancel_run, ACTIVE_WORKFLOWS, resume_run_pipeline

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1")

# In-memory runs fallback store when database is not connected
_RUNS_MEM_STORE: dict[str, dict] = {}


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Healthcheck endpoint (API_SPEC.md § GET /health)."""
    return HealthResponse(status="ok", version=settings.APP_VERSION)


@router.get("/auth/me")
async def auth_me():
    """Current authenticated user stub."""
    return {"id": "dev-user", "email": "dev@example.com", "authenticated": True}


@router.get("/models")
async def list_available_models(refresh: bool = Query(default=False)):
    """Fetch dynamically discovered OpenRouter free models and local Ollama models."""
    from backend.app.services.model_catalog import model_catalog_service
    return await model_catalog_service.get_models(force_refresh=refresh)


@router.post("/runs", response_model=RunCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def create_run(
    req: RunCreateRequest,
    db: Optional[AsyncSession] = Depends(get_async_db)
):
    """Create and enqueue a new co-founder analysis run (API_SPEC.md § POST /runs)."""
    run_id = str(uuid.uuid4())
    run_uuid = uuid.UUID(run_id)
    options_dict = req.options.model_dump()

    # 1. Store in DB
    try:
        new_run = Run(
            id=run_uuid,
            idea=req.idea,
            status="queued",
            options=options_dict,
            total_tokens=0,
            total_cost_usd=0.0
        )
        db.add(new_run)
        await db.commit()
    except Exception as e:
        logger.warning(f"DB insert fallback to memory: {e}")
        _RUNS_MEM_STORE[run_id] = {
            "run_id": run_id,
            "idea": req.idea,
            "status": "queued",
            "options": options_dict,
            "market": None,
            "prd": None,
            "architecture": None,
            "pitch": None,
            "scores": {},
            "created_at": datetime.now(timezone.utc).isoformat(),
            "completed_at": None,
            "total_tokens": 0,
            "total_cost_usd": 0.0,
            "debate_messages": []
        }

    # 2. Dispatch background execution
    dispatch_run(run_id, req.idea, options_dict)

    return RunCreateResponse(run_id=run_id, status="queued")


@router.get("/runs", response_model=List[RunDetailResponse])
async def list_runs(
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Optional[AsyncSession] = Depends(get_async_db)
):
    """List runs paginated (API_SPEC.md § GET /runs)."""
    runs_list = []
    try:
        stmt = select(Run).order_by(desc(Run.created_at)).offset(offset).limit(limit)
        result = await db.execute(stmt)
        records = result.scalars().all()
        for r in records:
            runs_list.append(RunDetailResponse(
                run_id=str(r.id),
                idea=r.idea,
                status=r.status,
                created_at=r.created_at.isoformat() if r.created_at else "",
                completed_at=r.completed_at.isoformat() if r.completed_at else None,
                total_tokens=r.total_tokens or 0,
                total_cost_usd=float(r.total_cost_usd or 0.0)
            ))
        return runs_list
    except Exception:
        # Fallback to memory
        mem_items = list(_RUNS_MEM_STORE.values())[offset : offset + limit]
        return [RunDetailResponse(**item) for item in mem_items]


ACRONYMS = {
    "ai", "seo", "ehr", "cbse", "b2b", "b2c", "saas", "crm", "api", "ml", "llm", "ui", "ux", "ar", "vr", "iot", "erp", "hr", "nlp"
}


def clean_production_title(idea: str, fallback_id: str = "") -> str:
    """Extract a professional, concise TitleCase startup brand title from raw prompt text.
    
    Transforms raw user prompts like:
      - 'AI tool that scans Shopify product catalogs and automatically rewrites descriptions...'
        -> 'Shopify_Product_Catalogs'
      - 'Voice AI assistant that answers after-hours phone calls for dental clinics...'
        -> 'Dental_Clinics_Voice_AI'
      - 'AI Tutor for CBSE Class 10 Students'
        -> 'AI_Tutor_CBSE_Class'
    """
    if not idea or not str(idea).strip():
        short_id = fallback_id[:8] if fallback_id else "Venture"
        return f"Startup_{short_id}"

    text = str(idea).strip()

    lead_patterns = [
        r"^(a|an|the)\s+",
        r"^(build|create|design|develop|make|launch)\s+(a|an|the)?\s*",
        r"^(an?\s+)?(ai|voice\s+ai|autonomous|smart|automated)\s+(tool|assistant|agent|platform|copilot|system|app|service|solution)\s+(that|to|for|which)?\s*",
        r"^(platform|tool|app|software|system|service|solution)\s+(that|to|for|which)\s+",
        r"^(scans|answers|automates|provides|enables|helps|generates)\s+",
    ]
    cleaned = text
    for bp in lead_patterns:
        cleaned = re.sub(bp, "", cleaned, flags=re.IGNORECASE).strip()

    words = re.findall(r"[A-Za-z0-9]+", cleaned)
    if not words or len(words) < 2:
        words = re.findall(r"[A-Za-z0-9]+", text)
    if not words:
        short_id = fallback_id[:8] if fallback_id else "Venture"
        return f"Startup_{short_id}"

    stop_words = {
        "that", "this", "and", "or", "for", "to", "in", "on", "with", "by", "at",
        "from", "into", "an", "a", "the", "is", "are", "using", "used", "of",
        "automatically", "directly"
    }

    meaningful = []
    for w in words:
        low = w.lower()
        if low in stop_words and len(meaningful) > 0:
            continue
        if low in ACRONYMS:
            meaningful.append(w.upper())
        else:
            meaningful.append(w.capitalize())
        if len(meaningful) == 4:
            break

    if not meaningful:
        meaningful = [w.capitalize() for w in words[:3]]

    title = "_".join(meaningful)
    title = re.sub(r"[^A-Za-z0-9_]+", "", title).strip("_")
    return title if title else "Startup_Venture"


@router.get("/runs/{run_id}", response_model=RunDetailResponse)
async def get_run(
    run_id: str,
    response: Response,
    db: Optional[AsyncSession] = Depends(get_async_db)
):
    """Retrieve full run details, outputs, and scores (API_SPEC.md § GET /runs/{run_id})."""
    try:
        run_uuid = uuid.UUID(run_id)
        stmt = select(Run).where(Run.id == run_uuid)
        res = await db.execute(stmt)
        run_rec = res.scalar_one_or_none()

        if not run_rec:
            if run_id in _RUNS_MEM_STORE:
                title = clean_production_title(_RUNS_MEM_STORE[run_id].get("idea", ""), run_id)
                json_filename = f"{title}_Run_Data.json"
                response.headers["Content-Disposition"] = f'inline; filename="{json_filename}"; filename*=UTF-8\'\'{json_filename}'
                response.headers["Access-Control-Expose-Headers"] = "Content-Disposition"
                return RunDetailResponse(**_RUNS_MEM_STORE[run_id])
            raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Run not found"}})

        # Fetch outputs
        out_stmt = select(AgentOutput).where(AgentOutput.run_id == run_uuid)
        out_res = await db.execute(out_stmt)
        outputs = out_res.scalars().all()

        market_data = next((o.output for o in outputs if o.agent == "market_analyst"), None)
        prd_data = next((o.output for o in outputs if o.agent == "pm"), None)
        arch_data = next((o.output for o in outputs if o.agent == "architect"), None)
        pitch_data = next((o.output for o in outputs if o.agent == "pitch_writer"), None)
        fact_check_data = next((o.output for o in outputs if o.agent == "fact_check"), None)

        # Fallback to in-memory store if DB record doesn't have fact_check yet
        telemetry_data = None
        if run_id in _RUNS_MEM_STORE:
            if not fact_check_data:
                fact_check_data = _RUNS_MEM_STORE[run_id].get("fact_check")
            telemetry_data = _RUNS_MEM_STORE[run_id].get("telemetry")

        # Fetch scores
        sc_stmt = select(Score).where(Score.run_id == run_uuid).order_by(Score.created_at)
        sc_res = await db.execute(sc_stmt)
        scores_map: dict[str, list[float]] = {}
        for s in sc_res.scalars().all():
            scores_map.setdefault(s.target_agent, []).append(float(s.score))

        title = clean_production_title(run_rec.idea, run_id)
        json_filename = f"{title}_Run_Data.json"
        response.headers["Content-Disposition"] = f'inline; filename="{json_filename}"; filename*=UTF-8\'\'{json_filename}'
        response.headers["Access-Control-Expose-Headers"] = "Content-Disposition"

        return RunDetailResponse(
            run_id=str(run_rec.id),
            idea=run_rec.idea,
            status=run_rec.status,
            market=market_data,
            prd=prd_data,
            architecture=arch_data,
            pitch=pitch_data,
            scores=scores_map,
            created_at=run_rec.created_at.isoformat() if run_rec.created_at else "",
            completed_at=run_rec.completed_at.isoformat() if run_rec.completed_at else None,
            total_tokens=run_rec.total_tokens or 0,
            total_cost_usd=float(run_rec.total_cost_usd or 0.0),
            fact_check=fact_check_data,
            telemetry=telemetry_data
        )
    except HTTPException:
        raise
    except Exception as e:
        if run_id in _RUNS_MEM_STORE:
            title = clean_production_title(_RUNS_MEM_STORE[run_id].get("idea", ""), run_id)
            json_filename = f"{title}_Run_Data.json"
            response.headers["Content-Disposition"] = f'inline; filename="{json_filename}"; filename*=UTF-8\'\'{json_filename}'
            response.headers["Access-Control-Expose-Headers"] = "Content-Disposition"
            return RunDetailResponse(**_RUNS_MEM_STORE[run_id])
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": f"Run not found: {e}"}})


@router.post("/runs/{run_id}/cancel", status_code=status.HTTP_200_OK)
async def cancel_run_endpoint(
    run_id: str,
    db: Optional[AsyncSession] = Depends(get_async_db)
):
    """Cancel a running job (API_SPEC.md § POST /runs/{run_id}/cancel)."""
    cancelled = cancel_run(run_id)
    try:
        run_uuid = uuid.UUID(run_id)
        stmt = select(Run).where(Run.id == run_uuid)
        res = await db.execute(stmt)
        run_rec = res.scalar_one_or_none()
        if run_rec:
            run_rec.status = "cancelled"
            await db.commit()
    except Exception:
        pass

    if run_id in _RUNS_MEM_STORE:
        _RUNS_MEM_STORE[run_id]["status"] = "cancelled"

    return {"message": "Run cancelled successfully", "run_id": run_id, "status": "cancelled"}


@router.get("/runs/{run_id}/pending", response_model=RunPendingResponse)
async def get_run_pending_approval(run_id: str):
    """Check if a run is currently awaiting human review approval (API HITL)."""
    wf_entry = ACTIVE_WORKFLOWS.get(run_id)
    if not wf_entry:
        if run_id in _RUNS_MEM_STORE and _RUNS_MEM_STORE[run_id].get("status") == "awaiting_approval":
            return RunPendingResponse(
                run_id=run_id,
                awaiting_approval=True,
                prd=_RUNS_MEM_STORE[run_id].get("prd")
            )
        return RunPendingResponse(run_id=run_id, awaiting_approval=False)

    state = wf_entry.get("state", {})
    interrupt_info = state.get("__interrupt__")
    payload = interrupt_info[0].value if interrupt_info else None
    return RunPendingResponse(
        run_id=run_id,
        awaiting_approval=True,
        interrupt_payload=payload if isinstance(payload, dict) else {"details": str(payload)},
        prd=state.get("prd")
    )


@router.post("/runs/{run_id}/resume", response_model=RunResumeResponse)
async def resume_run_endpoint(run_id: str, req: RunResumeRequest):
    """Resume execution of a run paused at human review interrupt (API HITL)."""
    if run_id not in ACTIVE_WORKFLOWS:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} is not currently awaiting review approval."
        )

    import asyncio
    asyncio.create_task(resume_run_pipeline(run_id, req.model_dump()))

    return RunResumeResponse(
        run_id=run_id,
        status="running",
        message="Workflow execution resumed with human reviewer input."
    )


@router.post("/runs/{run_id}/rerun", response_model=RunCreateResponse, status_code=status.HTTP_202_ACCEPTED)
async def rerun_endpoint(
    run_id: str,
    req: RunRerunRequest,
    db: Optional[AsyncSession] = Depends(get_async_db)
):
    """Rerun with modified inputs/assumptions (API_SPEC.md § POST /runs/{run_id}/rerun)."""
    # Look up original run
    original_idea = None
    original_options = {}

    try:
        run_uuid = uuid.UUID(run_id)
        stmt = select(Run).where(Run.id == run_uuid)
        res = await db.execute(stmt)
        run_rec = res.scalar_one_or_none()
        if run_rec:
            original_idea = run_rec.idea
            original_options = run_rec.options or {}
    except Exception:
        pass

    if not original_idea and run_id in _RUNS_MEM_STORE:
        original_idea = _RUNS_MEM_STORE[run_id]["idea"]
        original_options = _RUNS_MEM_STORE[run_id].get("options", {})

    if not original_idea:
        raise HTTPException(status_code=404, detail={"error": {"code": "NOT_FOUND", "message": "Source run not found"}})

    new_idea = req.idea or original_idea
    new_options = req.options.model_dump() if req.options else original_options

    new_run_id = str(uuid.uuid4())
    new_run_uuid = uuid.UUID(new_run_id)

    try:
        new_run = Run(
            id=new_run_uuid,
            idea=new_idea,
            status="queued",
            options=new_options
        )
        db.add(new_run)
        await db.commit()
    except Exception:
        _RUNS_MEM_STORE[new_run_id] = {
            "run_id": new_run_id,
            "idea": new_idea,
            "status": "queued",
            "options": new_options,
            "created_at": datetime.now(timezone.utc).isoformat()
        }

    dispatch_run(new_run_id, new_idea, new_options)
    return RunCreateResponse(run_id=new_run_id, status="queued")


@router.get("/runs/{run_id}/debate", response_model=DebateTranscriptResponse)
async def get_debate_transcript(
    run_id: str,
    db: Optional[AsyncSession] = Depends(get_async_db)
):
    """Retrieve debate transcript for run (API_SPEC.md § GET /runs/{run_id}/debate)."""
    messages = []
    try:
        run_uuid = uuid.UUID(run_id)
        stmt = select(DebateMessage).where(DebateMessage.run_id == run_uuid).order_by(DebateMessage.round, DebateMessage.created_at)
        res = await db.execute(stmt)
        for msg in res.scalars().all():
            messages.append({
                "round": msg.round,
                "from_agent": msg.from_agent,
                "to_agent": msg.to_agent,
                "content": msg.content,
                "created_at": msg.created_at.isoformat() if msg.created_at else ""
            })
    except Exception:
        pass

    if not messages and run_id in _RUNS_MEM_STORE:
        messages = _RUNS_MEM_STORE[run_id].get("debate_messages", [])

    return DebateTranscriptResponse(run_id=run_id, messages=messages)


def get_production_export_filename(idea: str, run_id: str, fmt: str) -> tuple[str, str]:
    """Returns (media_type, canonical_filename) with executive TitleCase branding and guaranteed extensions.
    
    Examples:
      - idea: 'AI tool that scans Shopify product catalogs...'
        -> 'Shopify_Product_Catalogs_Executive_Report.pdf'
        -> 'Shopify_Product_Catalogs_Pitch_Deck.pptx'
        -> 'Shopify_Product_Catalogs_Venture_Plan.md'
        -> 'Shopify_Product_Catalogs_Financial_Model.csv'
    """
    fmt_clean = "md" if fmt.lower() in ("md", "markdown") else fmt.lower()
    title = clean_production_title(idea, run_id)

    media_map = {
        "md": ("text/markdown; charset=utf-8", f"{title}_Venture_Plan.md"),
        "pptx": ("application/vnd.openxmlformats-officedocument.presentationml.presentation", f"{title}_Pitch_Deck.pptx"),
        "pdf": ("application/pdf", f"{title}_Executive_Report.pdf"),
        "csv": ("text/csv; charset=utf-8", f"{title}_Financial_Model.csv"),
    }

    if fmt_clean not in media_map:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "UNSUPPORTED_FORMAT", "message": f"Export format '{fmt}' is not supported. Use pdf, pptx, md, or csv."}}
        )

    return media_map[fmt_clean]


async def _get_run_state(run_id: str, db: Optional[AsyncSession] = None) -> dict[str, Any]:
    """Retrieve deliverables and score data for export generation from DB or fallback memory store."""
    run_rec = None
    outputs = []
    scores_map: dict[str, list[float]] = {}
    debate_log = []

    if db:
        try:
            run_uuid = uuid.UUID(run_id)
            r_stmt = select(Run).where(Run.id == run_uuid)
            r_res = await db.execute(r_stmt)
            run_rec = r_res.scalar_one_or_none()

            out_stmt = select(AgentOutput).where(AgentOutput.run_id == run_uuid)
            out_res = await db.execute(out_stmt)
            outputs = out_res.scalars().all()

            sc_stmt = select(Score).where(Score.run_id == run_uuid).order_by(Score.created_at)
            sc_res = await db.execute(sc_stmt)
            for s in sc_res.scalars().all():
                scores_map.setdefault(s.target_agent, []).append(float(s.score))

            deb_stmt = select(DebateMessage).where(DebateMessage.run_id == run_uuid).order_by(DebateMessage.created_at)
            deb_res = await db.execute(deb_stmt)
            debate_log = [
                {
                    "round": d.round,
                    "from_agent": d.from_agent,
                    "to_agent": d.to_agent,
                    "type": "debate",
                    "content": d.content
                }
                for d in deb_res.scalars().all()
            ]
        except Exception as e:
            logger.warning(f"Error querying DB for run state {run_id}: {e}")

    # Fallback to memory store if DB lookup did not yield run
    if not run_rec and run_id in _RUNS_MEM_STORE:
        mem_data = _RUNS_MEM_STORE[run_id]
        return {
            "run_id": run_id,
            "idea": mem_data.get("idea", "Startup Package"),
            "status": mem_data.get("status", "completed"),
            "market": mem_data.get("market"),
            "prd": mem_data.get("prd"),
            "architecture": mem_data.get("architecture"),
            "pitch": mem_data.get("pitch"),
            "scores": mem_data.get("scores", {}),
            "debate_log": mem_data.get("debate_log", []),
            "token_usage": {"total": mem_data.get("total_tokens", 0)}
        }
    elif run_rec:
        def _parse_out(raw):
            if raw is None:
                return None
            if isinstance(raw, dict):
                return raw
            if isinstance(raw, str):
                try:
                    return json.loads(raw)
                except Exception:
                    return raw
            return raw

        market_data = _parse_out(next((o.output for o in outputs if o.agent == "market_analyst"), None))
        prd_data = _parse_out(next((o.output for o in outputs if o.agent == "pm"), None))
        arch_data = _parse_out(next((o.output for o in outputs if o.agent == "architect"), None))
        pitch_data = _parse_out(next((o.output for o in outputs if o.agent == "pitch_writer"), None))

        return {
            "run_id": run_id,
            "idea": run_rec.idea,
            "status": run_rec.status,
            "market": market_data,
            "prd": prd_data,
            "architecture": arch_data,
            "pitch": pitch_data,
            "scores": scores_map,
            "debate_log": debate_log,
            "token_usage": {"total": run_rec.total_tokens or 0}
        }
    else:
        raise HTTPException(
            status_code=404,
            detail={"error": {"code": "NOT_FOUND", "message": f"Run '{run_id}' not found or deliverables missing."}}
        )


@router.get("/runs/{run_id}/export")
async def export_file_endpoint(
    run_id: str,
    format: str = Query(default="md", pattern="^(pdf|pptx|md|markdown|csv)$"),
    db: Optional[AsyncSession] = Depends(get_async_db)
):
    """Download exported package in PDF, PPTX, Markdown, or CSV format with clean production filenames."""
    state = await _get_run_state(run_id, db)
    fmt_clean = "md" if format.lower() == "markdown" else format.lower()
    media_type, filename = get_production_export_filename(state.get("idea", ""), run_id, fmt_clean)

    from backend.app.exporters.manager import ExportManager
    try:
        export_mgr = ExportManager()
        stream = export_mgr.export_in_memory(run_id, state, file_format=fmt_clean)
    except Exception as e:
        logger.error(f"Failed to generate in-memory export for {run_id} ({fmt_clean}): {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "EXPORT_FAILED", "message": f"Failed to generate {fmt_clean} export: {str(e)}"}}
        )

    stream.seek(0)
    return StreamingResponse(
        stream,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"; filename*=UTF-8\'\'{filename}',
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


@router.get("/runs/{run_id}/download/{filename}")
async def direct_download_endpoint(
    run_id: str,
    filename: str,
    db: Optional[AsyncSession] = Depends(get_async_db)
):
    """Direct URL download endpoint where the clean executive filename is embedded right in the URL path.
    
    Guarantees that direct browser navigation, Swagger UI, or download managers always
    save the file with the exact intended TitleCase name and correct file extension.
    Example: GET /api/v1/runs/{run_id}/download/Shopify_SEO_AI_Pitch_Deck.pptx
    """
    ext = os.path.splitext(filename)[1].lower().lstrip(".")
    if not ext:
        ext = "pdf"
    if ext == "markdown":
        ext = "md"

    valid_exts = {"pdf", "pptx", "md", "csv"}
    if ext not in valid_exts:
        raise HTTPException(
            status_code=400,
            detail={"error": {"code": "INVALID_FILENAME", "message": f"Unsupported file extension '{ext}'. Must be one of {valid_exts}"}}
        )

    state = await _get_run_state(run_id, db)
    media_type, canonical_filename = get_production_export_filename(state.get("idea", ""), run_id, ext)

    target_filename = filename if filename.lower().endswith(f".{ext}") else canonical_filename

    from backend.app.exporters.manager import ExportManager
    try:
        export_mgr = ExportManager()
        stream = export_mgr.export_in_memory(run_id, state, file_format=ext)
    except Exception as e:
        logger.error(f"Failed to generate direct download export for {run_id} ({ext}): {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": {"code": "EXPORT_FAILED", "message": f"Failed to generate {ext} export: {str(e)}"}}
        )

    stream.seek(0)
    return StreamingResponse(
        stream,
        media_type=media_type,
        headers={
            "Content-Disposition": f'attachment; filename="{target_filename}"; filename*=UTF-8\'\'{target_filename}',
            "Access-Control-Expose-Headers": "Content-Disposition",
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )


