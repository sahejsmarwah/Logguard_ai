"""
logguard/agent/planner.py
--------------------------
LLM-based planner that decides which investigation steps to run.

Allowed investigation steps (run by the Executor):
  - fetch_logs     : Load & store provided logs into findings
  - identify_code  : Locate the faulty source file and read it

The Validator always runs automatically after the Executor finishes (via the graph).
"""
import json
import re
from logguard.llm import call_llm

ALLOWED_STEPS = {"fetch_logs", "identify_code"}

SYSTEM_PROMPT = """
You are an SRE incident response planner for Python applications.

Your job is to decide which investigation steps are needed BEFORE the root-cause analysis.

Available steps:
- fetch_logs      : Load the error logs into context for the LLM analyst.
- identify_code   : Find and read the source file referenced in the stack trace.

Rules:
- Always include "fetch_logs" if there are error logs to process.
- Always include "identify_code" if a file path or project root is provided.
- Keep the plan minimal — order matters (fetch_logs before identify_code).
- Do NOT include a "validate" step; that runs automatically after your steps finish.

Respond ONLY as a JSON array of strings.
Example: ["fetch_logs", "identify_code"]
"""


def _extract_json(text: str) -> str:
    match = re.search(r"\[.*?\]", text, re.DOTALL)
    if not match:
        raise ValueError(f"No JSON array found in:\n{text}")
    return match.group()


def create_plan(service: str, severity: str, additional_context: str = None) -> list:
    """
    Ask the LLM to produce an ordered list of investigation steps.

    Args:
        service:            Name of the affected service/script.
        severity:           "low" / "medium" / "high" / "critical".
        additional_context: Optional extra guidance (from [m] re-analysis feedback).

    Returns:
        List of step names (strings).
    """
    user_prompt = f"""Incident detected.

Service:  {service}
Severity: {severity}
"""
    if additional_context:
        user_prompt += f"\nAdditional focus for this re-investigation:\n{additional_context}\n"

    user_prompt += "\nChoose only the necessary investigation steps."

    try:
        response = call_llm(SYSTEM_PROMPT, user_prompt, model="llama-3.3-70b-versatile")
        plan = json.loads(_extract_json(response))

        if not isinstance(plan, list):
            raise ValueError("Plan is not a list")

        # Sanitize: only keep known allowed steps
        sanitized = []
        for item in plan:
            if isinstance(item, str) and item in ALLOWED_STEPS:
                sanitized.append(item)
            elif isinstance(item, dict):
                for v in list(item.values()) + list(item.keys()):
                    if isinstance(v, str) and v in ALLOWED_STEPS:
                        sanitized.append(v)
                        break

        return sanitized if sanitized else ["fetch_logs", "identify_code"]

    except Exception:
        # Safe fallback
        return ["fetch_logs", "identify_code"]
