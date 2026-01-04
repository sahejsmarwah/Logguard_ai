from logguard.tools.logs import get_logs
from logguard.tools.deployments import get_deployments
from logguard.tools.health import check_health
from logguard.tools.code_context import get_code_context
from logguard.utils.log_utils import truncate_logs

def execute(step: str, state):
    if step == "fetch_logs":
        # Use provided logs if available, else fetch default (mock)
        logs = state.provided_logs if state.provided_logs else get_logs()
        state.findings["logs"] = truncate_logs(logs)
        state.reasoning_trace.append(f"Executed step: {step}")

    elif step == "check_deployments":
        state.findings["deployments"] = get_deployments()
        state.reasoning_trace.append(f"Executed step: {step}")

    elif step == "check_health":
        state.findings["health"] = check_health()
        state.reasoning_trace.append(f"Executed step: {step}")

    elif step == "identify_code":
        # Use configured target file if available
        # Handle dict or object
        target_path = state.target_file_path
        
        if not target_path:
             state.reasoning_trace.append(f"Executed step: {step} | Skipped (No target path provided)")
        else:
            # Check if target is a directory (Project Root)
            import os
            from logguard.utils.file_finder import find_faulty_file
            
            if os.path.isdir(target_path):
                logs = state.findings.get("logs", []) or state.provided_logs or []
                found_file = find_faulty_file(target_path, logs)
                
                if found_file:
                    target_path = found_file
                    # Update state with the specific file so subsequent steps use it
                    state.target_file_path = found_file
                    state.reasoning_trace.append(f"Executed step: {step} | Auto-discovered file: {found_file}")
                else:
                    state.reasoning_trace.append(f"Executed step: {step} | Failed to find specific file in {target_path}")

            ctx = get_code_context(target_path)
            state.code_context["metrics_service"] = ctx
            state.reasoning_trace.append(f"Executed step: {step}")

    elif step == "run_reproduction":
        from logguard.tools.test_runner import run_test_script
        
        repro_script = state.reproduction_script
        
        if repro_script:
             with open("repro_test.py", "w") as f:
                 f.write(repro_script)
        
        result = run_test_script("repro_test.py")
        
        state.findings["reproduction_result"] = result
        state.reasoning_trace.append(f"Executed step: {step} | Success: {result['success']}")

    elif step == "verify_fix":
        from logguard.tools.simulator import apply_patch, restore_backup
        from logguard.tools.test_runner import run_test_script
        
        # 1. Apply Patch
        # Use configured path if available, else skip
        target_file = state.target_file_path
        
        if not target_file:
             # Cannot verify without a target file
             result = {"success": False, "error": "No target file to verify against"}
             state.findings["verification_result"] = result
             return state
        
        # Use fixed_code_content if available, else fall back (but we expect content now)
        patch_content = state.fixed_code_content or state.suggested_fix
        
        if patch_content:
             apply_patch(target_file, patch_content)
        
        # 2. Run Test again
        result = run_test_script("repro_test.py")
        
        state.findings["verification_result"] = result
        state.reasoning_trace.append(f"Executed step: {step} | Verified: {result['success']}")
        
        # 3. Restore (cleanup) so we don't mess up user environment permanently until approval
        restore_backup(target_file)

    return state
