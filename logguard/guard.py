import sys
import subprocess
import argparse
from logguard.services.incident_manager import handle_incident

def run_guard():
    parser = argparse.ArgumentParser(description="LogGuard Runtime Monitor")
    parser.add_argument("script", help="The python script to run")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments for the script")
    
    args = parser.parse_args()
    
    script_path = args.script
    script_args = args.args
    
    print(f"🛡️ LogGuard monitoring: {script_path} {' '.join(script_args)}")
    print("-" * 50)

    try:
        # Run the user's script
        # Capture stderr to feed to the agent if it crashes
        cmd = [sys.executable, script_path] + script_args
        process = subprocess.run(
            cmd,
            stdout=sys.stdout, # Stream stdout directly to console
            stderr=subprocess.PIPE, # Capture stderr
            text=True
        )

        # Standard Error Output Handling
        if process.stderr:
            print(process.stderr, file=sys.stderr) # Print stderr to console as well

        if process.returncode != 0:
            print("\n" + "-" * 50)
            print("🚨 CRASH DETECTED! LogGuard is taking over...")
            print("-" * 50)
            
            # Prepare logs from stderr
            logs_content = [{"message": line.strip(), "level": "ERROR"} for line in process.stderr.splitlines() if line.strip()]
            
            # Initial simple heuristic: if no stderr but non-zero exit, maybe it printed to stdout or just silently failed.
            if not logs_content:
                logs_content = [{"message": f"Process exited with code {process.returncode}", "level": "ERROR"}]

            handle_incident(
                service=script_path,
                severity="critical",
                target_file_path=script_path,
                logs=logs_content
            )
            
        else:
            print("\n✅ Process exited successfully.")

    except KeyboardInterrupt:
        print("\nUsing stopping monitor.")
    except Exception as e:
        print(f"Monitor Warning: {e}")

if __name__ == "__main__":
    run_guard()
