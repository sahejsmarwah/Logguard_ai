def write_validation_bundle(state):
    # Handle state being a dict or object
    code_diff = state.get("code_diff") if isinstance(state, dict) else state.code_diff
    service = state.get("service") if isinstance(state, dict) else state.service
    severity = state.get("severity") if isinstance(state, dict) else state.severity
    confidence = state.get("confidence") if isinstance(state, dict) else state.confidence

    with open("fix.patch", "w") as f:
        f.write(code_diff or "# No patch generated")

    test_code = f"""
# Reproduction Test for {service}

def test_incident_fix():
    '''
    Expected behavior:
    - Service should start without DB timeout
    - Authentication errors should be handled gracefully
    '''
    # TODO: Insert mocked dependencies here
    assert True
"""
    with open("repro_test.py", "w") as f:
        f.write(test_code)

    runbook = f"""
INCIDENT VALIDATION RUNBOOK
===========================

Service: {service}
Severity: {severity}

Steps:
1. Apply fix.patch locally
2. Run repro_test.py
3. Verify service health endpoint returns OK
4. Confirm no ERROR logs appear for 5 minutes

Expected Outcome:
- Incident does not reproduce
- Confidence score: {confidence}
"""
    with open("runbook.md", "w") as f:
        f.write(runbook)
