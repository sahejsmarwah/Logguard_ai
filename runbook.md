INCIDENT VALIDATION RUNBOOK
===========================

Service:    test-svc
Severity:   high
Confidence: 92.00%

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
