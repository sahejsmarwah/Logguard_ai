from pydantic import BaseModel
from typing import Dict, Optional

class IncidentState(BaseModel):
    incident_id: str
    service: str
    severity: str
    current_step: str
    code_diff: str | None = None
    reasoning_trace: list[str] = []
    requires_human_approval: bool = False
    recommended_action: str | None = None

    findings: Dict = {}
    code_context: Dict = {}

    root_cause: Optional[str] = None
    suggested_fix: Optional[str] = None
    fixed_code_content: Optional[str] = None
    reproduction_script: Optional[str] = None
    confidence: float = 0.0
    
    # Configuration
    target_file_path: Optional[str] = None
    provided_logs: Optional[list] = None
