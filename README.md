# 🛡️ LogGuard AI

**The Autonomous Incident Response Agent.**

LogGuard AI is not just a logger; it's an **AI-powered SRE** that lives in your terminal. When your code crashes, LogGuard detects it, investigates the root cause, reproduces the issue with a test case, plans a fix, and—with your approval—**patches your code automatically**.

---

## 🚀 Features

- **Runtime Guard**: Wrap any script (`logguard my_app.py`). If it crashes, LogGuard catches it and fixes it in real-time.
- **Log Watcher**: Monitor log files of running services (`logguard watch`). Perfect for servers/Docker.
- **Auto-Discovery**: Support for large projects. Give it the project root, and it finds the faulty file automatically from the stack trace.
- **Self-Verification**: It doesn't guess. It writes a reproduction script, verifies the bug exists, applies the fix, and runs the test again to prove it works.

## 📦 Installation

```bash
# Clone the repo
git clone <repo-url>
cd Logguard_ai

# Install configuration
# Create a .env file with your Groq API Key
echo "GROQ_API_KEY=gsk_..." > .env

# Install the tool
pip install .
```

## 🛠️ Usage

### 1. The "Zero-Touch" Guard
Best for running scripts, workers, or during development.
```bash
logguard my_script.py
```
*If `my_script.py` crashes, LogGuard wakes up and fixes it.*

### 2. The Log Watcher
Best for large applications, servers, or background processes.
```bash
logguard watch --logs /var/log/app.log --project /path/to/project
```
*LogGuard tails the file. As soon as a traceback appears, it triggers an investigation.*

### 3. Post-Mortem Analysis
Best for analyzing a crash that happened in the past.
```bash
logguard analyze --logs crash_dump.txt --project .
```

## 🧠 How it Works
See [ARCHITECTURE.md](ARCHITECTURE.md) for a deep dive into the internal Agentic Loop, LangGraph architecture, and decision-making process.

## 🤝 Contributing
Built with 💙 using **LangGraph**, **Groq**, and **Python**.
