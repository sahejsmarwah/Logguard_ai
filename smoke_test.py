"""Quick smoke tests for the new LogGuard v0.2 modules."""
import os
import tempfile

# ── Test 1: find_error_line ───────────────────────────────────────────────────
from logguard.utils.file_finder import find_error_line

fake_log = (
    "Traceback (most recent call last):\n"
    '  File "/project/logguard/guard.py", line 42, in run_guard\n'
    "    process = subprocess.run(cmd)\n"
    "AttributeError: something broke\n"
)
line = find_error_line(fake_log, "/project/logguard/guard.py")
assert line == 42, f"Expected 42, got {line}"
print(f"[PASS] find_error_line returns: {line}")

# ── Test 2: get_code_context with error_line ──────────────────────────────────
from logguard.tools.code_context import get_code_context

with tempfile.NamedTemporaryFile(
    suffix=".py", mode="w", delete=False, encoding="utf-8"
) as f:
    f.write("\n".join(f"# line {i}" for i in range(1, 101)))
    tmp = f.name

ctx = get_code_context(tmp, error_line=50, context_lines=5)
assert ">>>" in ctx, "Error marker missing"
assert "50" in ctx, "Error line number missing"
print("[PASS] get_code_context with error_line marker")
os.unlink(tmp)

# ── Test 3: validation_bundle generates real diff ────────────────────────────
from logguard.agent.state import IncidentState
from logguard.actions.validation_bundle import write_validation_bundle

state = IncidentState(
    incident_id="TEST-1",
    service="test-svc",
    severity="high",
    confidence=0.92,
    fixed_code_content='print("fixed")\n',
    reproduction_script="def test_repro():\n    assert True\n",
    target_file_path="/tmp/foo.py",
)

write_validation_bundle(state, original_content='print("broken")\n')

assert os.path.exists("fix.patch"), "fix.patch not created"
patch = open("fix.patch", encoding="utf-8").read()
assert "-print" in patch and "+print" in patch, f"Bad patch: {patch!r}"
print(f"[PASS] fix.patch contains real diff ({len(patch)} chars)")

assert os.path.exists("repro_test.py"), "repro_test.py not created"
repro = open("repro_test.py", encoding="utf-8").read()
assert "test_repro" in repro, "AI repro test content missing"
print("[PASS] repro_test.py contains actual AI-generated test")

assert os.path.exists("runbook.md"), "runbook.md not created"
print("[PASS] runbook.md created")

# ── Test 4: config loads and creates default file ────────────────────────────
from logguard.config import get_config, CONFIG_FILE
cfg = get_config()
assert "auto_fix" in cfg
assert "auto_fix_threshold" in cfg
assert CONFIG_FILE.exists(), "Config file was not created"
print(f"[PASS] config loaded: auto_fix={cfg['auto_fix']} threshold={cfg['auto_fix_threshold']}")

# ── Test 5: incident_log ──────────────────────────────────────────────────────
from logguard.utils.incident_log import log_incident, get_all_incidents, mark_fix_applied
entry = log_incident(state)
assert entry["incident_id"] == "TEST-1"
all_inc = get_all_incidents()
assert any(i["incident_id"] == "TEST-1" for i in all_inc)
mark_fix_applied("TEST-1")
updated = get_all_incidents()
assert any(i["incident_id"] == "TEST-1" and i["fix_applied"] for i in updated)
print("[PASS] incident_log: write, read, mark_fix_applied all work")

print("\nALL SMOKE TESTS PASSED")
