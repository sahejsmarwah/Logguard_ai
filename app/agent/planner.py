import json
import re
from app.llm import call_llm

SYSTEM_PROMPT = """
You are an SRE incident response planner.

Your job is to decide which investigation steps are required.
Return steps in execution order.

Allowed steps:
- fetch_logs
- check_deployments
- check_health
- identify_code
- validate

Respond ONLY as JSON list.
"""

def extract_json(text: str):
    match = re.search(r"\[.*\]", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON array found:\n{text}")
    return match.group()

def create_plan(service: str, severity: str):
    user_prompt = f"""
Incident detected.

Service: {service}
Severity: {severity}

Choose only the necessary investigation steps.
"""

    response = call_llm(SYSTEM_PROMPT, user_prompt)

    plan = json.loads(extract_json(response))
    return plan
