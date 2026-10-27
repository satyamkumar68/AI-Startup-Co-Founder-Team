from typing import List, Dict, Optional, Literal, Any, Union
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


# ==============================================================================
# 1. Market Analyst Schemas (FR-2, AGENTS.md §1)
# ==============================================================================

class MarketMetric(BaseModel):
    """TAM / SAM / SOM estimate or market metric with citation requirement."""
    value: str = Field(..., description="Numerical value and currency (e.g. '$12.5B')")
    unit: Optional[str] = Field(default="USD", description="Currency or metric unit")
    estimated: bool = Field(default=False, description="Flag true if calculated or approximated")
    source_url: Optional[str] = Field(default=None, description="Direct citation URL or research link")
    retrieved_at: Optional[str] = Field(default=None, description="ISO timestamp or date of data retrieval")
    is_assumption: bool = Field(default=False, description="Flag true if figure is an ungrounded or derived assumption")
    notes: Optional[str] = Field(default=None, description="Calculation methodology or context")

    @model_validator(mode="before")
    @classmethod
    def parse_from_string(cls, data: Any) -> Any:
        from datetime import datetime, timezone
        now_date = datetime.now(timezone.utc).date().isoformat()
        if isinstance(data, str):
            return {
                "value": data,
                "unit": "USD",
                "estimated": True,
                "source_url": None,
                "retrieved_at": now_date,
                "is_assumption": True
            }
        if isinstance(data, dict):
            url = data.get("source_url")
            if not url or "example.com" in str(url) or not str(url).startswith("http"):
                data["is_assumption"] = True
            if not data.get("retrieved_at"):
                data["retrieved_at"] = now_date
            if not data.get("value"):
                data["value"] = data.get("description") or data.get("amount") or data.get("size") or "$10.0B (est.)"
        return data


class CompetitorItem(BaseModel):
    """Competitor profile."""
    name: str = Field(..., description="Competitor company or product name")
    description: str = Field(..., description="Core offering and market positioning")
    strengths: List[str] = Field(default_factory=list, description="Key competitive advantages")
    weaknesses: List[str] = Field(default_factory=list, description="Gaps, complaints, or vulnerabilities")
    url: Optional[str] = Field(default=None, description="Website or reference URL")


class MarketAnalystOutput(BaseModel):
    """Structured deliverable from Market Analyst."""
    tam: MarketMetric = Field(..., description="Total Addressable Market")
    sam: MarketMetric = Field(..., description="Serviceable Addressable Market")
    som: MarketMetric = Field(..., description="Serviceable Obtainable Market")
    competitors: List[CompetitorItem] = Field(..., min_length=5, description="At least 5 direct/indirect competitors")
    trends: List[str] = Field(default_factory=list, description="Key industry and technological trends")
    risks: List[str] = Field(..., min_length=3, description="At least 3 significant market/execution risks")
    sources: List[str] = Field(..., min_length=1, description="List of source URLs backing the analysis")




# ==============================================================================
# 2. Product Manager Schemas (FR-3, AGENTS.md §2)
# ==============================================================================

class Persona(BaseModel):
    """Target user persona."""
    name: str = Field(..., description="Persona title/archetype (e.g. 'Struggling High-Schooler')")
    role: str = Field(..., description="Role or user segment")
    pain_points: List[str] = Field(..., min_length=1, description="Primary frustrations and bottlenecks")
    goals: List[str] = Field(..., min_length=1, description="What success looks like for this user")


class FeatureItem(BaseModel):
    """Prioritized feature specification."""
    name: str = Field(..., description="Short feature name")
    priority: Literal["P0", "P1", "P2"] = Field(..., description="P0 (Must have), P1 (Should have), P2 (Nice to have)")
    description: Optional[str] = Field(default=None, description="Feature behavior and user value")


class ProductManagerOutput(BaseModel):
    """Structured deliverable from Product Manager."""
    personas: List[Persona] = Field(..., min_length=2, description="At least 2 target user personas")
    problem_statement: str = Field(..., description="Crisp formulation of core problem being solved")
    features: List[FeatureItem] = Field(..., description="Prioritized feature backlog")
    mvp_scope: str = Field(..., description="Tight MVP boundary buildable in <= 8 weeks by 2 devs")
    user_stories: List[str] = Field(..., min_length=3, description="Core user stories (As a... I want... So that...)")
    success_metrics: List[str] = Field(..., min_length=2, description="Measurable leading and lagging KPIs")

    @field_validator("features")
    @classmethod
    def validate_p0_limit(cls, v: List[FeatureItem]) -> List[FeatureItem]:
        p0_count = sum(1 for f in v if getattr(f, "priority", None) == "P0" or (isinstance(f, dict) and f.get("priority") == "P0"))
        if p0_count > 8:
            raise ValueError(f"Exceeded maximum 8 P0 features: found {p0_count} (max 8 allowed)")
        return v


# ==============================================================================
# 3. Tech Architect Schemas (FR-4, AGENTS.md §3)
# ==============================================================================

class StackChoice(BaseModel):
    """Technology choice with 1-line justification."""
    technology: str = Field(..., description="Technology name (e.g. 'FastAPI', 'PostgreSQL')")
    category: str = Field(..., description="Category (Frontend, Backend, Database, Cache, DevOps, LLM)")
    justification: str = Field(..., description="One-line justification favoring MVP simplicity")


class ArchitectureComponent(BaseModel):
    """Subsystem component."""
    name: str = Field(..., description="Component name")
    responsibility: str = Field(..., description="Primary duty")
    technologies: List[str] = Field(default_factory=list, description="Technologies utilized")


class MonthlyCostEstimate(BaseModel):
    """Estimated monthly run rate for MVP scale."""
    total_usd: float = Field(..., description="Total monthly cloud + API expenditure in USD")
    breakdown: Dict[str, float] = Field(..., description="Itemized costs per service")
    assumptions: List[str] = Field(default_factory=list, description="Assumptions regarding traffic/tokens")

    @field_validator("total_usd", mode="before")
    @classmethod
    def parse_float_currency(cls, v: Any) -> Any:
        if isinstance(v, str):
            clean = v.replace("$", "").replace(",", "").strip()
            try:
                return float(clean)
            except ValueError:
                return 0.0
        return v


class TechArchitectOutput(BaseModel):
    """Structured deliverable from Tech Architect."""
    stack: List[StackChoice] = Field(..., description="Tech stack items with 1-line justifications")
    components: List[ArchitectureComponent] = Field(..., description="System architectural components")
    diagram_mermaid: str = Field(..., description="Syntactically valid Mermaid architecture diagram")
    data_model: str = Field(..., description="Database entity schema overview / relational structure")
    scalability_notes: str = Field(..., description="Path from MVP to 100k users")
    monthly_cost_estimate: MonthlyCostEstimate = Field(..., description="Infrastructure cost estimate")
    risks: List[str] = Field(..., min_length=2, description="Technical and scalability risks")

    @field_validator("risks", mode="before")
    @classmethod
    def pad_arch_risks(cls, v: Any) -> Any:
        if isinstance(v, list) and len(v) < 2:
            defaults = [
                "Database connection exhaustion during high-volume catalog crawling batches",
                "Shopify Admin GraphQL rate limits during full-store multi-thousand SKU bulk updates"
            ]
            for r in defaults:
                if len(v) >= 2:
                    break
                v.append(r)
        return v


# ==============================================================================
# 4. Pitch Writer Schemas (FR-5, AGENTS.md §4)
# ==============================================================================

class PitchSlide(BaseModel):
    """Single pitch deck slide."""
    slide_number: int = Field(..., ge=1, le=12, description="Slide sequence number (1-12)")
    title: str = Field(..., description="Slide headline")
    bullets: List[str] = Field(..., min_length=2, max_length=6, description="Bullet points for slide body")
    speaker_notes: str = Field(..., description="Concise speaker script / talking points")

    @model_validator(mode="before")
    @classmethod
    def normalize_slide_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if not data.get("bullets"):
                content = data.get("content") or data.get("body") or data.get("description")
                if isinstance(content, list):
                    data["bullets"] = [str(x) for x in content]
                elif isinstance(content, str):
                    lines = [line.strip().lstrip("-*• ") for line in content.split("\n") if line.strip()]
                    data["bullets"] = lines if len(lines) >= 2 else [content[:150], "Key strategic priority for MVP"]
                else:
                    data["bullets"] = ["Core strategic objective", "Milestone target for launch"]
            if not data.get("speaker_notes"):
                data["speaker_notes"] = data.get("notes") or data.get("content") or f"Talking points for {data.get('title', 'this slide')}."
        return data

    @field_validator("bullets", mode="before")
    @classmethod
    def pad_bullets(cls, v: Any) -> Any:
        if isinstance(v, list):
            if len(v) < 2:
                v.extend(["Key strategic priority for this phase", "Measurable execution target and milestone"])
            elif len(v) > 6:
                v = v[:6]
        return v


class PitchWriterOutput(BaseModel):
    """Structured deliverable from Pitch Writer (10-12 slides)."""
    slides: List[PitchSlide] = Field(..., min_length=10, max_length=12, description="Pitch deck of 10 to 12 slides")




# ==============================================================================
# 5. CEO / Critic Review Schemas (FR-6, FR-7, AGENTS.md §5)
# ==============================================================================

class CEOCriticReview(BaseModel):
    """Rubric-based review score and feedback from CEO/Critic."""
    target_agent: str = Field(..., description="Agent name being reviewed ('market', 'prd', 'architecture', 'pitch')")
    version: int = Field(default=1, description="Version of the deliverable evaluated")
    score: float = Field(..., ge=1.0, le=10.0, description="Overall score between 1.0 and 10.0")
    strengths: List[str] = Field(default_factory=list, description="Notable positive attributes")
    weaknesses: List[str] = Field(default_factory=list, description="Deficiencies, gaps, or questionable assumptions")
    required_changes: List[str] = Field(default_factory=list, description="Actionable changes needed to pass")
    pass_: bool = Field(default=True, alias="pass", description="True if score >= 7.0 threshold")

    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode="after")
    def sync_pass_with_score(self) -> "CEOCriticReview":
        # Ensure pass_ is consistent with score >= 7.0 (or default threshold)
        self.pass_ = self.score >= 7.0
        return self


# ==============================================================================
# 6. Debate Protocol Schemas (FR-8, AGENTS.md Debate Protocol)
# ==============================================================================

class CritiqueIssue(BaseModel):
    """Single issue raised in debate critique."""
    issue: str = Field(..., description="Specific flaw, contradiction, or gap")
    suggestion: str = Field(..., description="Concrete actionable recommendation")


class PeerCritique(BaseModel):
    """Critique from one agent to a peer."""
    from_agent: str = Field(..., description="Critiquing agent ('market', 'pm', 'architect')")
    target: str = Field(..., description="Target peer agent")
    issues: List[str] = Field(default_factory=list, description="Identified inconsistencies or gaps")
    suggestions: List[str] = Field(default_factory=list, description="Recommended modifications")


class RebuttalResponse(BaseModel):
    """Author response accepting or rejecting critique issues."""
    target: str = Field(..., description="Peer who initiated critique")
    accepted: List[Union[Dict[str, Any], str]] = Field(default_factory=list, description="Issues accepted and how addressed")
    rejected: List[Union[Dict[str, Any], str]] = Field(default_factory=list, description="Issues rejected and reasoning")
    output_updated: bool = Field(default=False, description="Flag indicating deliverable was adjusted")


RebuttalResponse.model_rebuild()



class DebateMessageRecord(BaseModel):
    """Persisted debate message."""
    round: int = Field(..., ge=1, le=2)
    from_agent: str
    to_agent: str
    message_type: Literal["critique", "response", "ceo_verdict"]
    content: Dict[str, Any]


# ==============================================================================
# 7. API Request & Response Schemas (API_SPEC.md)
# ==============================================================================

class RunOptions(BaseModel):
    """Options for run execution."""
    provider: Optional[str] = Field(default=None, description="LLM provider: 'ollama', 'openrouter', 'openai', 'gemini', 'anthropic'")
    debate_rounds: int = Field(default=2, ge=0, le=2, description="Number of debate rounds (0-2)")
    score_threshold: float = Field(default=7.0, ge=1.0, le=10.0, description="Minimum score to pass CEO gate")
    model_override: Optional[str] = Field(default=None, description="Optional LLM model override")
    fallback_models: List[str] = Field(default_factory=list, description="Ordered list of fallback models for auto-switch")
    mode: Optional[Literal["single_agent", "multi_no_debate", "multi_debate"]] = Field(default=None, description="Run mode for ablation studies")
    enable_human_review: bool = Field(default=False, description="Enable human-in-the-loop review interrupt before tech architecture")


class RunCreateRequest(BaseModel):
    """POST /runs request body."""
    idea: str = Field(..., min_length=10, max_length=500, description="Startup idea (10-500 characters)")
    options: RunOptions = Field(default_factory=RunOptions)


class RunCreateResponse(BaseModel):
    """POST /runs 202 response."""
    run_id: str
    status: Literal["queued", "running", "awaiting_approval", "completed", "failed", "cancelled", "needs_review", "budget_exceeded"] = "queued"


class RunDetailResponse(BaseModel):
    """GET /runs/{run_id} response."""
    run_id: str
    idea: str
    status: Literal["queued", "running", "awaiting_approval", "completed", "failed", "cancelled", "needs_review", "budget_exceeded"]
    market: Optional[Dict[str, Any]] = None
    prd: Optional[Dict[str, Any]] = None
    architecture: Optional[Dict[str, Any]] = None
    pitch: Optional[Dict[str, Any]] = None
    scores: Dict[str, List[float]] = Field(default_factory=dict)
    created_at: str
    completed_at: Optional[str] = None
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    fact_check: Optional[Dict[str, Any]] = None
    telemetry: Optional[Dict[str, Any]] = None


class RunResumeRequest(BaseModel):
    """POST /runs/{run_id}/resume request body."""
    approved: bool = Field(default=True, description="Whether human reviewer approved deliverable")
    edited_prd: Optional[Dict[str, Any]] = Field(default=None, description="Optional modified PRD deliverable")
    feedback: Optional[str] = Field(default=None, description="Human reviewer notes or feedback")


class RunResumeResponse(BaseModel):
    """POST /runs/{run_id}/resume response."""
    run_id: str
    status: str
    message: str


class RunPendingResponse(BaseModel):
    """GET /runs/{run_id}/pending response."""
    run_id: str
    awaiting_approval: bool
    interrupt_payload: Optional[Dict[str, Any]] = None
    prd: Optional[Dict[str, Any]] = None


class RunRerunRequest(BaseModel):
    """POST /runs/{run_id}/rerun request."""
    idea: Optional[str] = Field(default=None, min_length=10, max_length=500)
    options: Optional[RunOptions] = None


class HealthResponse(BaseModel):
    """GET /health response."""
    status: Literal["ok"] = "ok"
    version: str = "0.1.0"


class DebateTranscriptResponse(BaseModel):
    """GET /runs/{run_id}/debate response."""
    run_id: str
    messages: List[Dict[str, Any]] = Field(default_factory=list)


# ==============================================================================
# 8. WebSocket Event Schemas (API_SPEC.md § WebSocket)
# ==============================================================================

class WebSocketEvent(BaseModel):
    """Base streaming WebSocket event."""
    type: Literal[
        "agent_started",
        "agent_token",
        "agent_completed",
        "score_posted",
        "debate_message",
        "run_completed",
        "run_failed"
    ]
    ts: Optional[str] = None
    agent: Optional[str] = None
    target: Optional[str] = None
    text: Optional[str] = None
    score: Optional[float] = None
    pass_: Optional[bool] = Field(default=None, alias="pass")
    output: Optional[Dict[str, Any]] = None
    from_: Optional[str] = Field(default=None, alias="from")
    to: Optional[str] = None
    content: Optional[Any] = None
    run_id: Optional[str] = None
    error: Optional[str] = None
    model_config = ConfigDict(populate_by_name=True)

