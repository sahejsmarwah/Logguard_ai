"""
logguard/guard.py
-----------------
Runtime Guard — wraps a Python script as a subprocess.
If the script crashes, LogGuard investigates and (optionally) restarts it.
"""
import sys
import subprocess
import argparse
from logguard.services.incident_manager import handle_incident
from logguard.config import get_config


def run_guard():
    parser = argparse.ArgumentParser(description="LogGuard Runtime Monitor")
    parser.add_argument("script", help="The Python script to run")
    parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments for the script")
    args = parser.parse_args()

    script_path = args.script
    script_args = args.args
    config      = get_config()

    print(f"🛡️  LogGuard monitoring: {script_path} {' '.join(script_args)}")
    print("─" * 50)

    cmd = [sys.executable, script_path] + script_args

    while True:
        try:
            process = subprocess.run(
                cmd,
                stdout=sys.stdout,      # Stream stdout live
                stderr=subprocess.PIPE, # Capture stderr for the agent
                text=True,
            )
        except FileNotFoundError:
            print(f"❌ Script not found: {script_path}")
            break
        except KeyboardInterrupt:
            print("\n\nStopping LogGuard monitor.")
            break

        # Print stderr so the user sees it too
        if process.stderr:
            print(process.stderr, file=sys.stderr)

        if process.returncode == 0:
            print("\n✅ Process exited successfully.")
            break

        # ── Crash detected ────────────────────────────────────────────────────
        print("\n" + "─" * 50)
        print("🚨 CRASH DETECTED — LogGuard is taking over…")
        print("─" * 50)

        logs_content = [
            {"message": line.strip(), "level": "ERROR"}
            for line in process.stderr.splitlines()
            if line.strip()
        ]
        if not logs_content:
            logs_content = [
                {"message": f"Process exited with code {process.returncode}", "level": "ERROR"}
            ]

        result = handle_incident(
            service=script_path,
            severity="critical",
            target_file_path=script_path,
            logs=logs_content,
            config=config,
        )

        # ── Offer restart if a fix was applied ────────────────────────────────
        if result and getattr(result, "fix_applied", False):
            print()
            try:
                choice = input("🔄  Fix applied! Restart the script? [y/n]: ").lower().strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if choice == "y":
                print(f"\n🔄  Restarting {script_path}…\n")
                continue   # Loop back and re-run the script
            else:
                break
        else:
            break


if __name__ == "__main__":
    run_guard()
