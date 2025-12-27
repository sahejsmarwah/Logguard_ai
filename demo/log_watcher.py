import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

import time
import ast
import json
from app.services.incident_manager import handle_incident

STATE_FILE = "demo/state.json"
LOG_FILE = "demo/runtime.log"

def load_state():
    with open(STATE_FILE, "r") as f:
        return json.load(f)

def save_state(state):
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)

def watch_logs():
    with open(LOG_FILE, "r") as f:
        f.seek(0, 2)

        while True:
            line = f.readline()
            if not line:
                time.sleep(1)
                continue

            log = ast.literal_eval(line.strip())

            state = load_state()
            state["latest_logs"].append(log)
            state["latest_logs"] = state["latest_logs"][-50:]

            if log["level"] == "ERROR":
                print("🚨 ERROR detected — triggering Logguard AI")

                result = handle_incident(
                    service="payment-service",
                    severity="high"
                )

                state["current_incident"] = result

            save_state(state)

if __name__ == "__main__":
    watch_logs()
