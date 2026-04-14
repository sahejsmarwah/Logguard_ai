"""
logguard/services/incident_manager.py
--------------------------------------
Orchestrates the full incident lifecycle:
  1. Build initial state
  2. Run the LangGraph pipeline
  3. Notify + log the incident
  4. Auto-fix (if confidence threshold met) OR prompt for human approval
  5. Human approval: show colored diff → [a]pprove / [r]eject / [m]ore analysis
"""
import os
import difflib
import logging

from logguard.utils.logger import setup_logger
from logguard.graph.graph import build_graph
from logguard.agent.state import IncidentState
from logguard.tools.simulator import apply_patch
from logguard.config import get_config

import time

# Module-level logger (reconfigured by CLI before first use)
logger = setup_logger()


# ── Public API ────────────────────────────────────────────────────────────────

def handle_incident(
    service: str,
    severity: str,
    target_file_path: str = None,
    logs: list = None,
    config: dict = None,
) -> IncidentState:
    """
    Entry point for all three operation modes (guard / watcher / analyze).

    Returns:
        The final IncidentState (fix_applied=True if a patch was written).
    """
    if config is None:
        config = get_config()

    logger.warning(f"🚨 Incident detected — service: {service}  severity: {severity}")

    # ── Cache original file content for diff generation ───────────────────────
    original_content = None
    if target_file_path and os.path.isfile(target_file_path):
        try:
            with open(target_file_path, "r", encoding="utf-8", errors="replace") as f:
                original_content = f.read()
        except Exception:
            pass

    state = IncidentState(
        incident_id=f"INC-{int(time.time())}",
        service=service,
        severity=severity,
        current_step="start",
        target_file_path=target_file_path,
        provided_logs=logs,
    )

    logger.info("🧠 Starting autonomous investigation…")

    # ── Run the LangGraph pipeline ────────────────────────────────────────────
    result = build_graph().invoke(state)
    if isinstance(result, dict):
        result = IncidentState(**result)

    # ── Refresh original_content if file-finder narrowed the path ────────────
    if result.target_file_path and result.target_file_path != target_file_path:
        if os.path.isfile(result.target_file_path) and original_content is None:
            try:
                with open(result.target_file_path, "r", encoding="utf-8", errors="replace") as f:
                    original_content = f.read()
            except Exception:
                pass

    # ── Notify ───────────────────────────────────────────────────────────────
    from logguard.actions.notifier import send_notification
    send_notification(
        f"LogGuard: Incident in {service}",
        f"Root cause: {result.root_cause or 'Unknown'}  |  "
        f"Confidence: {result.confidence:.0%}",
    )

    # ── Persist incident + report ─────────────────────────────────────────────
    from logguard.utils.incident_log import log_incident, save_report
    log_incident(result)
    report_path = save_report(result)

    _log_results(result)
    logger.info(f"📋 Report saved: {report_path}")

    # ── Auto-fix or human approval ────────────────────────────────────────────
    auto_fix       = config.get("auto_fix", False)
    threshold      = float(config.get("auto_fix_threshold", 0.85))

    if auto_fix and result.confidence >= threshold:
        logger.info(
            f"🤖 Auto-fix triggered — confidence {result.confidence:.0%} "
            f">= threshold {threshold:.0%}"
        )
        _apply_fix(result, original_content, auto=True)
    else:
        if auto_fix and result.confidence < threshold:
            logger.warning(
                f"⚠️  Auto-fix skipped — confidence {result.confidence:.0%} "
                f"< threshold {threshold:.0%}. Requesting human review."
            )
        _human_intervention(result, original_content, config)

    # ── Update log entry with final fix_applied status ────────────────────────
    if result.fix_applied:
        from logguard.utils.incident_log import mark_fix_applied
        mark_fix_applied(result.incident_id)

    return result


# ── Internal helpers ──────────────────────────────────────────────────────────

def _log_results(state: IncidentState):
    """Print a summary of the investigation findings."""
    logger.info("─" * 50)
    logger.info("🔍 Investigation complete")
    logger.info(f"📌 Root cause:  {state.root_cause or 'Unknown'}")
    logger.info(f"📊 Confidence:  {state.confidence:.2%}")
    logger.info(f"🎯 Recommended: {state.recommended_action or 'N/A'}")

    if "reproduction_result" in state.findings:
        repro = state.findings["reproduction_result"]
        label = "FAILED (bug confirmed ✓)" if not repro["success"] else "PASSED (unexpected)"
        logger.info(f"🧪 Repro test:  {label}")

    if "verification_result" in state.findings:
        verify = state.findings["verification_result"]
        label  = "PASSED (fix works ✓)" if verify["success"] else "FAILED ✗"
        logger.info(f"✅ Fix verify:  {label}")

    if state.suggested_fix:
        logger.info("🛠  Suggested fix:")
        for line in state.suggested_fix.strip().split("\n"):
            logger.info(f"   {line}")
    logger.info("─" * 50)


def _print_diff(original: str, fixed: str, filepath: str = None):
    """Print a syntax-colored unified diff to the terminal."""
    original_lines = original.splitlines(keepends=True)
    fixed_lines    = fixed.splitlines(keepends=True)
    fname = os.path.basename(filepath) if filepath else "source.py"

    diff = list(difflib.unified_diff(
        original_lines, fixed_lines,
        fromfile=f"a/{fname}", tofile=f"b/{fname}",
    ))

    if not diff:
        print("\n(No textual changes detected in the file.)\n")
        return

    # ANSI colors
    GREEN  = "\033[92m"
    RED    = "\033[91m"
    CYAN   = "\033[96m"
    RESET  = "\033[0m"
    BOLD   = "\033[1m"

    print(f"\n{'─' * 60}")
    print(f"{BOLD}📋  PROPOSED CHANGES  ({fname}){RESET}")
    print(f"{'─' * 60}")
    for line in diff:
        if line.startswith("+") and not line.startswith("+++"):
            print(f"{GREEN}{line}{RESET}", end="")
        elif line.startswith("-") and not line.startswith("---"):
            print(f"{RED}{line}{RESET}", end="")
        elif line.startswith("@@"):
            print(f"{CYAN}{line}{RESET}", end="")
        else:
            print(line, end="")
    print(f"{'─' * 60}\n")


def _apply_fix(state: IncidentState, original_content: str, auto: bool = False):
    """Write the fix to disk, generate the validation bundle."""
    final_content = getattr(state, "fixed_code_content", None)
    target_path   = getattr(state, "target_file_path", None)

    if not final_content:
        logger.warning("⚠️  No fixed code content available — cannot apply fix")
        return

    if not target_path or not os.path.isfile(target_path):
        logger.warning("⚠️  No valid target file — cannot apply fix")
        return

    try:
        apply_patch(target_path, final_content, backup=True)
        state.fix_applied = True

        from logguard.actions.validation_bundle import write_validation_bundle
        write_validation_bundle(state, original_content)

        prefix = "🤖 Auto-fix" if auto else "✅ Fix"
        logger.info(f"{prefix} applied to: {target_path}")
        logger.info("📦 Saved: fix.patch  repro_test.py  runbook.md")
    except Exception as e:
        logger.error(f"❌ Failed to apply fix: {e}")


def _human_intervention(
    state: IncidentState,
    original_content: str,
    config: dict,
):
    """
    Interactive prompt: show the diff, then [a]pprove / [r]eject / [m]ore analysis.
    """
    logger.warning("🧑‍✈️  Human approval required")

    # Show the diff so the user knows what they're approving
    if original_content and state.fixed_code_content:
        _print_diff(original_content, state.fixed_code_content, state.target_file_path)
    else:
        logger.warning("⚠️  No diff available (no original content or no fix generated)")

    while True:
        try:
            choice = input(
                "\nChoose action:\n"
                "  [a] Approve and apply fix\n"
                "  [r] Reject fix\n"
                "  [m] Request more analysis\n"
                "Your choice: "
            ).lower().strip()
        except (EOFError, KeyboardInterrupt):
            print()
            logger.info("Exiting approval prompt.")
            break

        if choice == "a":
            _apply_fix(state, original_content)
            break

        elif choice == "r":
            logger.info("❌ Fix rejected — no changes made")
            break

        elif choice == "m":
            feedback = input(
                "   What should the agent investigate further? "
                "(press Enter to skip): "
            ).strip()

            # Inject feedback so the planner can see it next run
            state.findings["additional_feedback"] = feedback or "Re-investigate with fresh eyes."
            # Clear consumed plan so planner re-plans from scratch
            state.findings.pop("execution_plan", None)

            logger.info("🔁 Re-running analysis with your feedback…")
            new_result = build_graph().invoke(state)
            if isinstance(new_result, dict):
                new_result = IncidentState(**new_result)

            # Update original_content if the file path changed
            new_original = original_content
            if (
                new_result.target_file_path
                and new_result.target_file_path != state.target_file_path
                and os.path.isfile(new_result.target_file_path)
            ):
                with open(new_result.target_file_path, "r", encoding="utf-8") as f:
                    new_original = f.read()

            _log_results(new_result)
            # Recurse — present the updated fix for approval
            _human_intervention(new_result, new_original, config)
            # Copy fix_applied status back
            state.fix_applied = new_result.fix_applied
            return

        else:
            logger.warning("⚠️  Invalid choice — please enter a, r, or m")
