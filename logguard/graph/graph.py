from langgraph.graph import StateGraph, END
from logguard.agent.state import IncidentState
from logguard.graph.nodes import planner_node, executor_node, validator_node, verification_node

def build_graph():
    graph = StateGraph(IncidentState)

    graph.add_node("planner", planner_node)
    graph.add_node("executor", executor_node)
    graph.add_node("validator", validator_node)

    graph.set_entry_point("planner")

    graph.add_node("verification", verification_node)

    graph.add_edge("planner", "executor")

    graph.add_conditional_edges(
        "executor",
        lambda state: "validator" if not state.findings.get("execution_plan") else "executor",
        {
            "executor": "executor",
            "validator": "validator",
        }
    )

    graph.add_edge("validator", "verification")
    graph.add_edge("verification", END)

    return graph.compile()
