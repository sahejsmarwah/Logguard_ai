"""
logguard/actions/validation_bundle.py
--------------------------------------
Writes the post-fix validation artifacts to the current directory:
  - fix.patch     : Real unified diff (original → fixed)
  - repro_test.py : The actual AI-generated reproduction test
  - runbook.md    : Step-by-step verification guide
"""
import difflib
import os


def write_validation_bundle(state, original_content: str = None):
    """
    Generate fix.patch, repro_test.py, and runbook.md.

    Args:
        state:            The final IncidentState.
        original_content: The raw original file content (before any fix).
                          Required to produce a meaningful diff.
    """
    # ── Helpers to handle dict or Pydantic state ──────────────────────────────
    def _get(attr, default=None):
        if isinstance(state, dict):
            return state.get(attr, default)
        return getattr(state, attr, default)

    service        = _get("service", "unknown")
    severity       = _get("severity", "unknown")
    confidence     = float(_get("confidence", 0.0))
    fixed_content  = _get("fixed_code_content")
    repro_script   = _get("reproduction_script")
    target_path    = _get("target_file_path")

    # ── 1. Real unified diff ──────────────────────────────────────────────────
    diff_text = "# No patch generated"
    if fixed_content and original_content:
        original_lines = original_content.splitlines(keepends=True)
        fixed_lines    = fixed_content.splitlines(keepends=True)
        fname = os.path.basename(target_path) if target_path else "source.py"
        diff_lines = list(difflib.unified_diff(
            original_lines,
            fixed_lines,
            fromfile=f"a/{fname}",
            tofile=f"b/{fname}",
        ))
        diff_text = "".join(diff_lines) if diff_lines else "# No changes detected"

    with open("fix.patch", "w", encoding="utf-8") as f:
        f.write(diff_text)

    # ── 2. Real AI-generated reproduction script ──────────────────────────────
    if repro_script:
        with open("repro_test.py", "w", encoding="utf-8") as f:
            f.write(repro_script)
    else:
        with open("repro_test.py", "w", encoding="utf-8") as f:
            f.write(
                f"# Reproduction test for: {service}\n"
                "# The agent did not generate a specific test.\n"
                "assert True  # placeholder\n"
            )

    # ── 3. Runbook ────────────────────────────────────────────────────────────
    runbook = f"""\
INCIDENT VALIDATION RUNBOOK
===========================

Service:    {service}
Severity:   {severity}
Confidence: {confidence:.2%}

Steps:
1. Review fix.patch — confirm the diff looks correct.
2. Run repro_test.py BEFORE applying the patch (it should FAIL, proving the bug).
   python repro_test.py
3. Apply the patch:
   patch -p1 < fix.patch
4. Run repro_test.py again (it should PASS, proving the fix).
   python repro_test.py
5. Run your full test suite.

Notes:
- A .bak backup of the original file is saved as <file>.bak
- Confidence >= 85% would have triggered auto-fix mode (if enabled in config).
"""
    with open("runbook.md", "w", encoding="utf-8") as f:
        f.write(runbook)
