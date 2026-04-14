"""
logguard/watcher.py
--------------------
Log Watcher — tails a log file and triggers the agent on error patterns.

Deduplication strategy:
  Content-hash based — identical error blocks (same exact lines) are silently
  skipped. Different errors always trigger fresh investigations.
"""
import time
import re
import os
import hashlib
from logguard.services.incident_manager import handle_incident
from logguard.config import get_config

# Regex that marks the start of an error block
ERROR_START_PATTERN = re.compile(
    r"Traceback \(most recent call last\):|ERROR|CRITICAL|Exception",
    re.IGNORECASE,
)


def watch_logs(log_path: str, project_root: str):
    """
    Tail log_path, buffer error blocks, and trigger incident response.

    Args:
        log_path:     Path to the log file to watch.
        project_root: Project root dir (passed to the incident manager).
    """
    config = get_config()
    dedup_enabled = config.get("watcher_dedup", True)

    print(f"👀 LogGuard Watcher active")
    print(f"   Log file:     {log_path}")
    print(f"   Project root: {project_root}")
    print(f"   Dedup:        {'on' if dedup_enabled else 'off'}")
    print("   Waiting for errors… (Ctrl+C to stop)\n")

    # Set of MD5 hashes of error blocks we've already handled this session
    seen_hashes: set = set()

    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            f.seek(0, os.SEEK_END)  # Start from the current end (tail -f style)

            buffer: list = []
            capturing   = False
            last_write  = time.time()

            while True:
                line = f.readline()

                if not line:
                    # Gap in log output — if we were capturing and have lines, flush
                    if capturing and buffer and (time.time() - last_write > 1.0):
                        _trigger_incident(buffer, project_root, config, seen_hashes, dedup_enabled)
                        buffer    = []
                        capturing = False
                    time.sleep(0.1)
                    continue

                last_write = time.time()

                # Detect start of an error block
                if ERROR_START_PATTERN.search(line):
                    if not capturing:
                        capturing = True
                        print("🚨 Error pattern detected — capturing…")

                if capturing:
                    buffer.append(line)

    except FileNotFoundError:
        print(f"❌ Log file not found: {log_path}")
    except KeyboardInterrupt:
        print("\nStopping watcher.")


def _trigger_incident(
    log_lines: list,
    project_root: str,
    config: dict,
    seen_hashes: set,
    dedup_enabled: bool,
):
    """Format and forward the captured error block to the incident manager."""
    if not log_lines:
        return

    # ── Content-hash deduplication ────────────────────────────────────────────
    if dedup_enabled:
        content_hash = hashlib.md5("".join(log_lines).encode("utf-8")).hexdigest()
        if content_hash in seen_hashes:
            print("⚠️  Duplicate error block — skipping (already handled this session)")
            return
        seen_hashes.add(content_hash)

    print(f"⚡ Triggering incident response ({len(log_lines)} lines captured)…")

    formatted_logs = [
        {"message": line.strip(), "level": "ERROR"}
        for line in log_lines
        if line.strip()
    ]

    handle_incident(
        service="watched-app",
        severity="high",
        target_file_path=project_root,
        logs=formatted_logs,
        config=config,
    )

    print("👀 Resuming watch…\n")
