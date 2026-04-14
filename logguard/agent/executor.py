"""
logguard/agent/executor.py
---------------------------
Executes one investigation step at a time.
Steps are: fetch_logs, identify_code, run_reproduction, verify_fix.
(check_health and check_deployments have been removed — they returned fake/empty data.)
"""
import os
from logguard.tools.code_context import get_code_context
from logguard.utils.log_utils import truncate_logs


def execute(step: str, state):
    """
    Execute a single investigation or verification step, mutating state in-place.

    Args:
        step:  Name of the step to run.
        state: The current IncidentState object.

    Returns:
        The (possibly mutated) state object.
    """

    # ── fetch_logs ────────────────────────────────────────────────────────────
    if step == "fetch_logs":
        logs = state.provided_logs if state.provided_logs else []
        state.findings["logs"] = truncate_logs(logs)
        state.reasoning_trace.append(
            f"[fetch_logs] Loaded {len(state.findings['logs'])} log lines"
        )

    # ── identify_code ─────────────────────────────────────────────────────────
    elif step == "identify_code":
        target_path = state.target_file_path

        if not target_path:
            state.reasoning_trace.append("[identify_code] Skipped — no target path provided")
        else:
            # If we got a directory, use the file-finder to locate the specific file
            if os.path.isdir(target_path):
                from logguard.utils.file_finder import find_faulty_file
                logs = state.findings.get("logs", []) or state.provided_logs or []
                found = find_faulty_file(target_path, logs)
                if found:
                    target_path = found
                    state.target_file_path = found
                    state.reasoning_trace.append(
                        f"[identify_code] Auto-discovered: {found}"
                    )
                else:
                    state.reasoning_trace.append(
                        f"[identify_code] Could not find specific file in {target_path}"
                    )

            # Extract error line for smart context reading
            error_line = None
            if os.path.isfile(target_path):
                from logguard.utils.file_finder import find_error_line
                logs = state.findings.get("logs", []) or state.provided_logs or []
                log_text = "\n".join([l.get("message", "") for l in logs])
                error_line = find_error_line(log_text, target_path)

            ctx = get_code_context(target_path, error_line=error_line)
            state.code_context["source"] = ctx
            state.reasoning_trace.append(
                f"[identify_code] Read {target_path}"
                + (f" — error at line {error_line}" if error_line else "")
            )

    # ── run_reproduction ──────────────────────────────────────────────────────
    elif step == "run_reproduction":
        from logguard.tools.test_runner import run_test_script

        repro = state.reproduction_script
        if repro:
            with open("repro_test.py", "w", encoding="utf-8") as f:
                f.write(repro)

        result = run_test_script("repro_test.py")
        state.findings["reproduction_result"] = result
        state.reasoning_trace.append(
            f"[run_reproduction] success={result['success']}"
        )

    # ── verify_fix ────────────────────────────────────────────────────────────
    elif step == "verify_fix":
        from logguard.tools.simulator import apply_patch, restore_backup
        from logguard.tools.test_runner import run_test_script

        target_file = state.target_file_path
        if not target_file:
            result = {"success": False, "output": "No target file to verify against"}
            state.findings["verification_result"] = result
            return state

        patch_content = state.fixed_code_content
        if patch_content:
            apply_patch(target_file, patch_content)

        result = run_test_script("repro_test.py")
        state.findings["verification_result"] = result
        state.reasoning_trace.append(
            f"[verify_fix] verified={result['success']}"
        )

        # Restore so we don't permanently alter the file until human approval
        restore_backup(target_file)

    else:
        state.reasoning_trace.append(f"[executor] Unknown step '{step}' — skipped")

    return state
