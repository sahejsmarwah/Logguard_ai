import argparse
import sys
from logguard.services.incident_manager import handle_incident

def main():
    parser = argparse.ArgumentParser(description="LogGuard AI Incident Response CLI")
    parser.add_argument("--service", type=str, default="payment-service", help="Name of the service")
    parser.add_argument("--severity", type=str, default="high", help="Severity level")
    parser.add_argument("--target", type=str, help="Path to the target source file (optional)")
    parser.add_argument("--logs", type=str, help="Path to a log file (optional)", default=None)
    
    args = parser.parse_args()

    print("\n🚨 LogGuard Interactive CLI 🚨")
    print("=================================")
    print("Press Ctrl+C to exit at any time.\n")
    
    try:
        service = args.service
        severity = args.severity
        target_file = args.target
        
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
        if target_file:
            print(f"Targeting file: {target_file}")
        
        result = handle_incident(
            service=service, 
            severity=severity,
            target_file_path=target_file,
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
