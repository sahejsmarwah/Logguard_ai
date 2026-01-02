import time
import re
import os
from logguard.services.incident_manager import handle_incident

# Regex to detect the START of a Python traceback or significant error
ERROR_START_PATTERN = re.compile(r'Traceback \(most recent call last\):|ERROR|CRITICAL|Exception')

def watch_logs(log_path: str, project_root: str):
    print(f"👀 LogGuard Watcher active.")
    print(f"    Target Log: {log_path}")
    print(f"    Project Root: {project_root}")
    print("    Waiting for errors... (Ctrl+C to stop)")

    # Open file and seek to end (tail -f style)
    try:
        with open(log_path, "r") as f:
            f.seek(0, os.SEEK_END)
            
            buffer = []
            capturing = False
            last_activity = time.time()
            
            while True:
                line = f.readline()
                if not line:
                    # If we were capturing and stopped getting lines for a bit, consider the error block "closed"
                    if capturing and (time.time() - last_activity > 2.0):
                        _trigger_incident(buffer, project_root)
                        buffer = []
                        capturing = False
                    
                    time.sleep(0.5)
                    continue
                
                # We have a line
                last_activity = time.time()
                
                # Check for start of error
                if ERROR_START_PATTERN.search(line):
                     if not capturing:
                         capturing = True
                         print("\n🚨 Error pattern detected! Capturing logs...")
                
                if capturing:
                    buffer.append(line)
                    
                    # If buffer gets too big, maybe flush it? 
                    # For now, rely on timeout to flush.
                    
    except FileNotFoundError:
        print(f"❌ Log file not found: {log_path}")
    except KeyboardInterrupt:
        print("\nStopping watcher.")

def _trigger_incident(log_lines: list, project_root: str):
    if not log_lines:
        return
        
    print(f"⚡ Triggering Incident Response with {len(log_lines)} log lines...")
    
    # Format logs for IncidentManager
    formatted_logs = [{"message": l.strip(), "level": "ERROR"} for l in log_lines]
    
    handle_incident(
        service="watched-app",
        severity="high",
        target_file_path=project_root, # Pass ROOT, not file. Executor will find the file.
        logs=formatted_logs
    )
    print("👀 Resuming watch...")
