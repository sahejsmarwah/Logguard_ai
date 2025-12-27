from app.agent.planner import create_plan
from app.agent.executor import execute
from app.agent.validator import validate

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
