"""
logguard/agent/state.py
------------------------
Pydantic model that carries all incident data through the LangGraph pipeline.
"""
from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class IncidentState(BaseModel):
    # ── Identity ──────────────────────────────────────────────────────────────
    incident_id: str
    service: str
    severity: str
    current_step: str = "start"

    # ── Investigation results ─────────────────────────────────────────────────
    findings: Dict = Field(default_factory=dict)
    code_context: Dict = Field(default_factory=dict)
    reasoning_trace: List[str] = Field(default_factory=list)

    # ── Analysis output (populated by Validator) ──────────────────────────────
    root_cause: Optional[str] = None
    suggested_fix: Optional[str] = None          # Human-readable description
    fixed_code_content: Optional[str] = None     # Full fixed file content
    reproduction_script: Optional[str] = None    # Python test that proves the bug
    code_diff: Optional[str] = None              # Unified diff (generated post-validation)
    confidence: float = 0.0

    # ── Recommendations ───────────────────────────────────────────────────────
    recommended_action: Optional[str] = None
    requires_human_approval: bool = True

    # ── Outcome ───────────────────────────────────────────────────────────────
    fix_applied: bool = False

    # ── Configuration passed in at incident creation ──────────────────────────
    target_file_path: Optional[str] = None
    provided_logs: Optional[List] = None
