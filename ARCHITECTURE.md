# LogGuard AI: Technical Deep Dive & Architecture

## 1. Overview
LogGuard AI is an **Autonomous Incident Response Agent**. It doesn't just "detect" errors; it investigates them like a human Site Reliability Engineer (SRE). It reads logs, analyzes stack traces, browses your code, plans a fix, validates it with a test, and then applies the patch—all automatically.

## 2. Core Philosophy
The system is built on an **Agentic Loop** using **LangGraph**. Unlike a standard script that runs A -> B -> C, LogGuard operates in a cycle:
1.  **Plan**: "What do I need to know to fix this?"
2.  **Execute**: "I'll read the file `payment.py` and checking the logs."
3.  **Reason**: "The logs say `ValueError`, and the code shows no try/except block."
4.  **Validate**: "I'll write a reproduction script to prove it fails."
5.  **Act**: "I'll patch the code and verify the test passes."

## 3. The Three Operation Modes

### A. Runtime Guard (`logguard <script>`)
**"Zero-Touch" Protection.**
- You run your script *through* LogGuard: `logguard my_script.py`.
- LogGuard wraps your process.
- If it crashes, LogGuard catches the `stderr`, automatically spins up the agent, fixes the code, and (optionally) restarts the process.
- **Best for:** Development scripts, simple workers, cron jobs.

### B. Log Watcher (`logguard watch`)
**"Sidecar" Monitoring.**
- Your app runs normally (Docker, Systemd, etc.).
- LogGuard tails your log file: `logguard watch --logs app.log --project .`.
- When it sees a crash trace, it triggers the agent.
- **Best for:** Production services, huge servers, complex deploys.

### C. Static Analysis (`logguard analyze`)
**"Post-Mortem" Forensics.**
- You have a crash log from last night.
- You point LogGuard to it: `logguard analyze --logs crash.log --project .`.
- It performs the investigation offline.

## 4. System Architecture

```mermaid
graph TD
    UserApp[User Application] -->|Crashes| LogSource[Logs / Stderr]
    LogSource -->|Trigger| IncidentManager[Incident Manager]
    
    subgraph "LogGuard Agent (LangGraph)"
        IncidentManager --> Planner
        Planner -->|Next Step| Executor
        Executor -->|Call Tool| Tools_Layer
        Tools_Layer -->|Result| Executor
        Executor -->|Loop| Planner
        Planner -->|Done| Validator
    end
    
    subgraph "Tools Layer"
        FileFinder[File Finder (Recursive Scan)]
        CodeReader[Code Context Reader]
        TestRunner[Test Runner (Reproduction)]
        Patcher[Patcher (Apply Fix)]
    end
    
    Validator -->|Success| HumanApproval[Human Approval]
    HumanApproval -->|Approve| Patcher
    Patcher -->|Write| UserApp
```

## 5. Key Components

### The Brain (`logguard/agent`)
- **Planner**: Decides the strategy. Uses detailed prompts to understand SRE methodologies.
- **Executor**: The "hands" of the agent. It calls tools based on the plan.
- **Validator**: The "QA". It writes a Python script (`repro_test.py`) to reproduce the bug and verifies the fix.

### The Tools (`logguard/tools`)
- **File Finder**: The "Eyes". If you give it a project root, it scans the directory tree using fuzzy matching and stack trace analysis to find *exactly* which file caused the crash.
- **Simulator**: Capable of applying patches and rolling them back if they fail verification.

### Connectivity (`logguard/llm.py`)
- Uses **Groq** (Llama 3 70B) for high-speed inference. It's set up to be plug-and-play with a simple API key.

## 6. Project Structure
- `logguard/`: Core package.
    - `agent/`: AI Logic.
    - `graph/`: LangGraph orchestration.
    - `tools/`: Interfaces for file I/O, testing, etc.
    - `watcher.py`: Logic for tailing logs.
    - `guard.py`: Logic for wrapping subprocesses.
- `setup.py`: Makes the whole thing installable as a CLI (`logguard`).
