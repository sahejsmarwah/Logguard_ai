from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from logguard.services.incident_manager import handle_incident

app = FastAPI(title="Incident Response AI Agent")

@app.post("/incident")
def run_incident(payload: dict):
    return handle_incident(
        service=payload["service"],
        severity=payload["severity"]
    )
