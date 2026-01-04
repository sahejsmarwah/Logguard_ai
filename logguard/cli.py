import argparse
import sys
import os
from logguard.services.incident_manager import handle_incident
from logguard.utils.log_utils import truncate_logs

def main():
    # Detect "logguard <script>.py" pattern for Runtime Guard
    if len(sys.argv) > 1 and sys.argv[1] not in ["analyze", "watch", "run"] and not sys.argv[1].startswith("-"):
        if sys.argv[1].endswith(".py") or os.path.exists(sys.argv[1]):
            from logguard.guard import run_guard
            run_guard()
            return

    parser = argparse.ArgumentParser(description="LogGuard AI Incident Response CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Run Command (Runtime Guard)
    run_parser = subparsers.add_parser("run", help="Run a python script through LogGuard monitoring")
    run_parser.add_argument("script", help="The python script to run")
    run_parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments for the script")

    # Analyze Command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze and fix a specific file or project")
    analyze_parser.add_argument("--service", type=str, default="payment-service", help="Name of the service")
    analyze_parser.add_argument("--severity", type=str, default="high", help="Severity level")
    analyze_parser.add_argument("--target", type=str, help="Path to the target source file (optional)")
    analyze_parser.add_argument("--project", type=str, help="Path to the project root (optional)")
    analyze_parser.add_argument("--logs", type=str, help="Path to a log file (optional)", default=None)
    
    # Watch Command
    watch_parser = subparsers.add_parser("watch", help="Watch a log file and auto-trigger on errors")
    watch_parser.add_argument("--logs", type=str, required=True, help="Path to the log file to watch")
    watch_parser.add_argument("--project", type=str, required=True, help="Path to the project root")

    # Parse args
    args = parser.parse_args()

    if args.command is None:
        parser.print_help()
        return

    print("\n🚨 LogGuard Interactive CLI 🚨")
    print("=================================")
    print("Press Ctrl+C to exit at any time.\n")
    
    try:
        if args.command == "run":
            from logguard.guard import run_guard
            # We need to manually adjust sys.argv for run_guard since it uses argparse too
            sys.argv = [sys.argv[0], args.script] + args.args
            run_guard()
            return

        if args.command == "watch":
            from logguard.watcher import watch_logs
            watch_logs(args.logs, args.project)
            return

        if args.command == "analyze":
            service = args.service
            severity = args.severity
            # Support both --target and --project. logic will be handled by executor
            target_path = args.target or args.project
            
            # Load logs if provided or auto-discover
            logs_content = None
            log_path = args.logs
            
            # Auto-discovery logic if no logs provided
            if not log_path and target_path and os.path.isdir(target_path):
                for common_log in ["app.log", "error.log"]:
                    potential_log = os.path.join(target_path, common_log)
                    if os.path.exists(potential_log):
                        log_path = potential_log
                        print(f"🔍 Auto-discovered log file: {log_path}")
                        break

            if log_path:
                try:
                    if os.path.exists(log_path):
                        with open(log_path, "r") as f:
                            raw_logs = [{"message": line.strip(), "level": "ERROR"} for line in f.readlines()]
                            logs_content = truncate_logs(raw_logs)
                            if len(logs_content) < len(raw_logs):
                                print(f"✂️ Logs truncated to last {len(logs_content)} lines to fit API limits.")
                    else:
                        print(f"⚠️ Warning: Log file '{log_path}' not found. Proceeding with analysis using context only.")
                except Exception as e:
                    print(f"⚠️ Warning: Could not read log file '{log_path}': {e}")
            else:
                print("ℹ️ No logs provided or discovered. Proceeding with static analysis.")

            print(f"Triggering incident for service='{service}'...")
            if target_path:
                print(f"Targeting: {target_path}")
            
            result = handle_incident(
                service=service, 
                severity=severity,
                target_file_path=target_path,
                logs=logs_content
            )
            
            print("\n✅ Incident Resolved!")
            if result:
                print(f"Final Confidence Score: {result.get('confidence')}")
        
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
