from app.tools.logs import get_logs
from app.tools.deployments import get_deployments
from app.tools.health import check_health
from app.tools.code_context import get_code_context

def execute(step: str, state):
    if step == "fetch_logs":
        state.findings["logs"] = get_logs()
        state.reasoning_trace.append(f"Executed step: {step}")

    elif step == "check_deployments":
        state.findings["deployments"] = get_deployments()
        state.reasoning_trace.append(f"Executed step: {step}")

    elif step == "check_health":
        state.findings["health"] = check_health()
        state.reasoning_trace.append(f"Executed step: {step}")

    elif step == "identify_code":
        # hardcoded for MVP – later auto-detect from logs
        state.code_context["payment_service"] = get_code_context(
            "app/mock_data/sample_code/payment_service.py"
        )
        state.reasoning_trace.append(f"Executed step: {step}")

    return state
