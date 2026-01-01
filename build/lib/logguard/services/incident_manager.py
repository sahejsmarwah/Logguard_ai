from logguard.utils.logger import setup_logger
from logguard.graph.graph import build_graph
from logguard.agent.state import IncidentState
import time
from logguard.actions.validation_bundle import write_validation_bundle
from logguard.tools.simulator import apply_patch
from logguard.utils.logger import setup_logger

logger = setup_logger()


def handle_incident(service: str, severity: str, target_file_path:str = None, logs: list = None):
    logger.warning(f"🚨 Incident detected in service: {service} | severity={severity}")

    state = IncidentState(
        incident_id=f"INC-{int(time.time())}",
        service=service,
        severity=severity,
        current_step="start",
        target_file_path=target_file_path,
        provided_logs=logs
    )

    logger.info("🧠 Starting autonomous investigation…")

    result = build_graph().invoke(state)

    log_results(result)
    human_intervention(result)

    return result

def log_results(state):
    logger.info("🔍 Investigation completed")

    logger.info(f"📌 Root cause identified:")
    logger.info(f"    {state.get('root_cause', 'Unknown')}")

    logger.info("🛠 Suggested fix:")
    suggested_fix = state.get("suggested_fix")
    if suggested_fix:
        for line in suggested_fix.split("\n"):
            logger.info(f"    {line}")
    else:
        logger.info("    No suggested fix available.")

    logger.info(f"📊 Confidence score: {state.get('confidence', 0.0):.2f}")
    
    findings = state.get("findings", {})
    if "reproduction_result" in findings:
        repro = findings["reproduction_result"]
        logger.info(f"🧪 Reproduction Test: {'FAILED (As Expected)' if not repro['success'] else 'PASSED (Unexpectedly)'}")
        
    if "verification_result" in findings:
        verify = findings["verification_result"]
        logger.info(f"✅ Verification Test: {'PASSED' if verify['success'] else 'FAILED'}")

def human_intervention(state):
    logger.warning("🧑‍✈️ Human approval required before remediation")

    while True:
        choice = input(
            "\nChoose action:\n"
            "  [a] Approve suggested fix\n"
            "  [r] Reject fix\n"
            "  [m] Ask agent for more analysis\n"
            "Your choice: "
        ).lower()

        if choice == "a":
            logger.info("✅ Fix approved by human operator")

            # 1. Generate bundle
            write_validation_bundle(state)
            logger.info("🧪 Validation bundle generated for local testing")

            # 2. Apply the fix physically to the code
            # Use fixed_code_content as it contains actual code, not description
            final_fix_content = state.get("fixed_code_content") if isinstance(state, dict) else state.fixed_code_content
            
            if final_fix_content:
                target_path = state.get("target_file_path") if isinstance(state, dict) else state.target_file_path
                
                if target_path:
                    try:
                        apply_patch(target_path, final_fix_content, backup=True)
                        logger.info(f"🚀 Fix applied to {target_path}")
                    except Exception as e:
                        logger.error(f"❌ Failed to apply fix to {target_path}: {e}")
                else:
                    logger.warning("⚠️ No 'target_file_path' provided. Cannot apply fix physically.")
            else:
                logger.warning("⚠️ No 'fixed_code_content' found to apply. 'suggested_fix' might just be a description.")

            break

        elif choice == "r":
            logger.info("❌ Fix rejected by human operator")
            break

        elif choice == "m":
            logger.info("🔁 Requesting further analysis from agent")
            feedback = input("   What should the agent check alongside? (optional): ")
            logger.info(f"   Feedback: {feedback}")
            logger.info("   ... restarting investigation (simulated for MVP) ...")
            # In a full recurring graph, we would update state and re-invoke. 
            # For simplicity, we'll just return early or 'continue' if we were in a loop.
            # But handle_incident returns 'result'. 
            # Let's break for now, but log that we would recurse.
            logger.info("   (Recursive analysis logic would trigger here)")
            break

        else:
            logger.warning("Invalid input, please choose again")


