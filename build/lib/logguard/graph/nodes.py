from logguard.agent.planner import create_plan
from logguard.agent.executor import execute
from logguard.agent.validator import validate

def planner_node(state):
    plan = create_plan(state.service, state.severity)
    state.findings["execution_plan"] = plan
    state.current_step = "planner"
    return state

def executor_node(state):
    plan = state.findings.get("execution_plan", [])

    if not plan:
        return state

    step = plan.pop(0)
    state.current_step = step
    state.findings["execution_plan"] = plan

    return execute(step, state)

def validator_node(state):
    state.current_step = "validate"
    return validate(state)

def verification_node(state):
    state.current_step = "verify"
    from logguard.agent.executor import execute
    
    # 1. Reproduce the issue (expect failure)
    state = execute("run_reproduction", state)
    
    # 2. Simulate fix and verify (expect success)
    state = execute("verify_fix", state)
    
    return state
