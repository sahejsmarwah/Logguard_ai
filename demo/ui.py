import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
load_dotenv()

import streamlit as st
import time
import json

STATE_FILE = "demo/state.json"

st.set_page_config(layout="wide")
st.title("🛡 Logguard AI – Live Incident Monitor")

log_col, incident_col = st.columns(2)

def load_state():
    with open(STATE_FILE, "r") as f:
        return json.load(f)

while True:
    state = load_state()

    with log_col:
        st.subheader("📜 Live Logs")
        st.json(state["latest_logs"])

    with incident_col:
        st.subheader("🤖 Logguard AI Analysis")
        if state["current_incident"]:
            st.json(state["current_incident"])
        else:
            st.info("Waiting for incident...")

    time.sleep(2)
    st.rerun()
