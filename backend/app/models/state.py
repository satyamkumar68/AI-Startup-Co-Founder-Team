from typing import TypedDict, Dict, List, Optional, Any


class RunState(TypedDict):
    """Shared workflow state across all agents and nodes in LangGraph.
    
    Adheres strictly to ARCHITECTURE.md §3.
    """
    run_id: str
    idea: str
    market: Optional[Dict[str, Any]]
    prd: Optional[Dict[str, Any]]
    architecture: Optional[Dict[str, Any]]
    pitch: Optional[Dict[str, Any]]
    scores: Dict[str, List[float]]
    debate_log: List[Dict[str, Any]]
    retries: Dict[str, int]
    token_usage: Dict[str, int]
    status: str
    
    # Extended execution tracking
    mode: Optional[str]
    telemetry: Optional[Dict[str, Any]]
    options: Dict[str, Any]
    current_agent: Optional[str]
    errors: List[str]
    debate_round: int
    user_id: Optional[str]
    _last_review: Optional[Dict[str, Any]]
    _debate_resolved: Optional[bool]
