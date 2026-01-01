import subprocess
import os

def run_test_script(test_script_path: str):
    """
    Executes a python test script and returns the result (pass/fail) and output.
    """
    if not os.path.exists(test_script_path):
        return {"success": False, "output": f"Test script not found: {test_script_path}"}
    
    try:
        result = subprocess.run(
            ["python", test_script_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        success = result.returncode == 0
        return {
            "success": success,
            "output": result.stdout + "\n" + result.stderr
        }
    except Exception as e:
        return {"success": False, "output": f"Failed to run test: {str(e)}"}
