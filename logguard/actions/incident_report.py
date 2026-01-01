def write_incident_report(state):
    report = f"""
INCIDENT REPORT
----------------
Service: {state.service}
Severity: {state.severity}

Root Cause:
{state.root_cause}

Suggested Fix:
{state.suggested_fix}

Confidence:
{state.confidence}
"""
    with open("incident_report.txt", "w") as f:
        f.write(report)
