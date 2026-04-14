"""
logguard/graph/nodes.py
------------------------
LangGraph node functions — thin wrappers that call into the agent modules.
"""
from logguard.agent.planner import create_plan
from logguard.agent.executor import execute
from logguard.agent.validator import validate


def planner_node(state):
    """Plan the investigation steps. Picks up any re-analysis feedback from findings."""
    additional_feedback = state.findings.get("additional_feedback")
    plan = create_plan(state.service, state.severity, additional_context=additional_feedback)

    state.findings["execution_plan"] = plan
    state.current_step = "planner"
    return state


def executor_node(state):
    """Pop and execute one step from the plan."""
    plan = state.findings.get("execution_plan", [])
    if not plan:
        return state

    step = plan.pop(0)
    state.current_step = step
    state.findings["execution_plan"] = plan

    return execute(step, state)


def validator_node(state):
    """Run LLM-based root-cause analysis and fix generation."""
    state.current_step = "validate"
    return validate(state)


def verification_node(state):
    """
    Self-verify the fix:
      1. Run reproduction script (expect FAIL — proves the bug exists).
      2. Apply the fix, run again (expect PASS — proves the fix works).
      3. Restore original file until human approves.
    """
    state.current_step = "verify"

    # 1. Reproduce (should fail)
    state = execute("run_reproduction", state)

    # 2. Apply patch, verify (should pass), then restore
    state = execute("verify_fix", state)

    return state
