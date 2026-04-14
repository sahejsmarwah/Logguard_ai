"""
logguard/utils/incident_log.py
------------------------------
Persistent incident logging and report saving.
  - incidents.log  : JSON-lines file, one entry per incident
  - reports/       : Human-readable .txt report per incident
"""
import json
import time
from pathlib import Path

from logguard.config import LOGGUARD_DIR

INCIDENTS_LOG = LOGGUARD_DIR / "incidents.log"
REPORTS_DIR = LOGGUARD_DIR / "reports"


def log_incident(state) -> dict:
    """Append a JSON line to ~/.logguard/incidents.log and return the entry."""
    LOGGUARD_DIR.mkdir(parents=True, exist_ok=True)

    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "incident_id": getattr(state, "incident_id", "unknown"),
        "service": getattr(state, "service", "unknown"),
        "severity": getattr(state, "severity", "unknown"),
        "root_cause": getattr(state, "root_cause", None),
        "confidence": round(float(getattr(state, "confidence", 0.0)), 4),
        "fix_applied": bool(getattr(state, "fix_applied", False)),
        "recommended_action": getattr(state, "recommended_action", None),
    }

    with open(INCIDENTS_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")

    return entry


def mark_fix_applied(incident_id: str):
    """Update the log entry for a given incident to set fix_applied=True."""
    if not INCIDENTS_LOG.exists():
        return

    lines = INCIDENTS_LOG.read_text(encoding="utf-8").splitlines()
    updated = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        try:
            entry = json.loads(line)
            if entry.get("incident_id") == incident_id:
                entry["fix_applied"] = True
            updated.append(json.dumps(entry))
        except Exception:
            updated.append(line)

    INCIDENTS_LOG.write_text("\n".join(updated) + "\n", encoding="utf-8")


def get_all_incidents() -> list:
    """Return all logged incidents as a list of dicts (oldest first)."""
    if not INCIDENTS_LOG.exists():
        return []

    incidents = []
    for line in INCIDENTS_LOG.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                incidents.append(json.loads(line))
            except Exception:
                pass
    return incidents


def save_report(state) -> str:
    """
    Save a human-readable incident report to ~/.logguard/reports/<timestamp>_<id>.txt.
    Returns the path to the saved file.
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    incident_id = getattr(state, "incident_id", "unknown")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"{timestamp}_{incident_id}.txt"

    reasoning = getattr(state, "reasoning_trace", [])
    reasoning_text = "\n  ".join(reasoning) if reasoning else "  None"

    report = f"""\
INCIDENT REPORT
===============
ID:           {incident_id}
Timestamp:    {time.strftime("%Y-%m-%d %H:%M:%S")}
Service:      {getattr(state, 'service', 'N/A')}
Severity:     {getattr(state, 'severity', 'N/A')}
Confidence:   {float(getattr(state, 'confidence', 0.0)):.2%}
Fix Applied:  {bool(getattr(state, 'fix_applied', False))}

ROOT CAUSE
----------
{getattr(state, 'root_cause', 'Unknown')}

SUGGESTED FIX
-------------
{getattr(state, 'suggested_fix', 'None')}

REASONING TRACE
---------------
  {reasoning_text}
"""

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    return str(report_path)
