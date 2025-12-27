import time
import random
from datetime import datetime

LOG_FILE = "demo/runtime.log"

LEVELS = ["INFO", "INFO", "INFO", "WARN", "ERROR"]

MESSAGES = {
    "INFO": "Service running normally",
    "WARN": "High memory usage detected",
    "ERROR": "Database connection failed"
}

def generate_logs():
    while True:
        level = random.choice(LEVELS)
        log = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": level,
            "service": "payment-service",
            "message": MESSAGES[level]
        }

        with open(LOG_FILE, "a") as f:
            f.write(str(log) + "\n")

        time.sleep(2)

if __name__ == "__main__":
    generate_logs()
