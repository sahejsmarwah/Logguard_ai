import argparse
import sys
from logguard.services.incident_manager import handle_incident

def main():
    parser = argparse.ArgumentParser(description="LogGuard AI Incident Response CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Analyze Command (Default)
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

    # If no subcommand is provided, assume "analyze" but check args
    args, unknown = parser.parse_known_args()
    if args.command is None:
        # Backward compatibility: if they just provided --target or nothing, assume analyze
        # But we need to re-parse with the analyze_parser to get defaults
        args = analyze_parser.parse_args()
        args.command = "analyze"
    else:
        args = parser.parse_args()

    print("\n🚨 LogGuard Interactive CLI 🚨")
    print("=================================")
    print("Press Ctrl+C to exit at any time.\n")
    
    try:
        if args.command == "watch":
            from logguard.watcher import watch_logs
            watch_logs(args.logs, args.project)
            return

        service = args.service
        severity = args.severity
        # Support both --target and --project. logic will be handled by executor
        target_path = args.target or args.project
        
        # Load logs if provided
        logs_content = None
        if args.logs:
            try:
                with open(args.logs, "r") as f:
                    logs_content = [{"message": line.strip(), "level": "ERROR"} for line in f.readlines()]
            except Exception as e:
                print(f"❌ Could not read log file: {e}")
                return

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
