import json
import re
from logguard.llm import call_llm

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

Respond ONLY as a JSON list of strings.
Example: ["fetch_logs", "check_health", "validate"]
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

    response = call_llm(SYSTEM_PROMPT, user_prompt, "llama-3.3-70b-versatile")

    try:
        plan = json.loads(extract_json(response))
        # Sanitize: Ensure list of strings
        if isinstance(plan, list):
            sanitized_plan = []
            for item in plan:
                if isinstance(item, str):
                    sanitized_plan.append(item)
                elif isinstance(item, dict):
                    # Try to find a value that matches a known step or just the first string value
                    # For now, simplistic approach: take the first string value found or keys
                    # This is a fallback; prompt engineering should ideally prevent this.
                    # Let's just try to extract the known allowed steps from values
                    allowed = {"fetch_logs", "check_deployments", "check_health", "identify_code", "validate"}
                    found = False
                    for v in item.values():
                        if isinstance(v, str) and v in allowed:
                            sanitized_plan.append(v)
                            found = True
                            break
                    if not found:
                         # key fallback
                         for k in item.keys():
                             if k in allowed:
                                 sanitized_plan.append(k)
                                 break
            plan = sanitized_plan
        return plan
    except Exception as e:
        # Fallback plan if parsing fails
        return ["fetch_logs", "check_health", "validate"]
