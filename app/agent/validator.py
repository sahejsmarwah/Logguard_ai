import json
import re
from app.llm import call_llm

SYSTEM_PROMPT = """
You are a senior backend engineer and SRE.

Given incident findings and relevant code:
1. Identify the most likely root cause
2. Suggest a concrete code-level fix
3. Generate a Git-style unified diff for the fix
4. Assign confidence (0.0 to 1.0)

Respond ONLY in valid JSON:
{
  "root_cause": "...",
  "suggested_fix": "...",
  "code_diff": "...",
  "reasoning_trace": ["..."],
  "confidence": 0.0
}
"""


def extract_json(text: str) -> str:
    """
    Extract the first JSON object from LLM output.
    Handles cases where the model adds extra text.
    """
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON found in LLM output:\n{text}")
    return match.group()

def validate(state):
    """
    Runs LLM-based validation to determine root cause and fix.
    """

    user_prompt = f"""
Incident Details:
Service: {state.service}
Severity: {state.severity}

Findings:
{json.dumps(state.findings, indent=2)}

Relevant Code:
{json.dumps(state.code_context, indent=2)}
"""

    response = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=user_prompt
    )

    try:
        json_str = extract_json(response)
        result = json.loads(json_str)
    except Exception as e:
        raise ValueError(
            f"Invalid LLM response received:\n{response}"
        ) from e

    # Update state
    state.root_cause = result.get("root_cause")
    state.suggested_fix = result.get("suggested_fix")
    state.code_diff = result.get("code_diff")
    state.reasoning_trace.extend(result.get("reasoning_trace", []))
    state.confidence = float(result.get("confidence", 0.0))
    if state.confidence < 0.6:
        state.recommended_action = "rollback_or_escalate"
        state.requires_human_approval = True
    elif state.confidence < 0.8:
        state.recommended_action = "human_review_required"
        state.requires_human_approval = True
    else:
        state.recommended_action = "auto_fix_safe"
        state.requires_human_approval = False


    return state
