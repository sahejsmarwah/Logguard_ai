from app.agent.state import IncidentState
from app.graph.graph import build_graph

graph = build_graph()

def handle_incident(service: str, severity: str, scenario: str = "db_failure"):
    state = IncidentState(
        incident_id="INC-001",
        service=service,
        severity=severity,
        current_step="start"
    )

    state.findings["scenario"] = scenario
    return graph.invoke(state)

