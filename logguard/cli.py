"""
logguard/cli.py
----------------
Main CLI entry point for LogGuard AI.

Commands:
  logguard <script>.py          — Runtime Guard (shortcut)
  logguard run <script> [args]  — Runtime Guard (explicit)
  logguard watch --logs <f> --project <dir>  — Log Watcher
  logguard analyze [options]    — Post-Mortem Analysis
  logguard status               — Show past incident history
  logguard config               — Show current config path & values
"""
import argparse
import sys
import os

from logguard.utils.log_utils import truncate_logs
from logguard.config import get_config, CONFIG_FILE, LOGGUARD_DIR


def main():
    # ── Shortcut: logguard my_script.py ──────────────────────────────────────
    if (
        len(sys.argv) > 1
        and sys.argv[1] not in ["analyze", "watch", "run", "status", "config"]
        and not sys.argv[1].startswith("-")
        and (sys.argv[1].endswith(".py") or os.path.exists(sys.argv[1]))
    ):
        _apply_global_flags()
        from logguard.guard import run_guard
        run_guard()
        return

    # ── Argument parser ───────────────────────────────────────────────────────
    parser = argparse.ArgumentParser(
        prog="logguard",
        description="🛡️  LogGuard AI — Autonomous Incident Response Agent",
    )

    # Global flags
    parser.add_argument("--verbose", "-v", action="store_true", help="Show full debug output")
    parser.add_argument("--quiet",   "-q", action="store_true", help="Only show warnings and errors")
    # Config overrides
    parser.add_argument("--auto-fix",           action="store_true", default=None,
                        help="Override config: enable auto-fix mode for this run")
    parser.add_argument("--no-auto-fix",         action="store_true", default=None,
                        help="Override config: disable auto-fix mode for this run")
    parser.add_argument("--auto-fix-threshold",  type=float, default=None,
                        help="Override config: confidence threshold for auto-fix (0.0–1.0)")

    subparsers = parser.add_subparsers(dest="command", help="Sub-command")

    # ── run ───────────────────────────────────────────────────────────────────
    run_parser = subparsers.add_parser("run", help="Run a script through LogGuard monitoring")
    run_parser.add_argument("script", help="Python script to run")
    run_parser.add_argument("args", nargs=argparse.REMAINDER, help="Arguments for the script")

    # ── analyze ───────────────────────────────────────────────────────────────
    analyze_parser = subparsers.add_parser("analyze", help="Post-mortem analysis of a crash")
    analyze_parser.add_argument("--service",  type=str, default="my-service", help="Service name label")
    analyze_parser.add_argument("--severity", type=str, default="high",
                                choices=["low", "medium", "high", "critical"])
    analyze_parser.add_argument("--target",   type=str, help="Path to specific source file (optional)")
    analyze_parser.add_argument("--project",  type=str, help="Path to project root (optional)")
    analyze_parser.add_argument("--logs",     type=str, default=None, help="Path to a log/crash dump file")

    # ── watch ─────────────────────────────────────────────────────────────────
    watch_parser = subparsers.add_parser("watch", help="Tail a log file and auto-trigger on errors")
    watch_parser.add_argument("--logs",    type=str, required=True, help="Log file to watch")
    watch_parser.add_argument("--project", type=str, required=True, help="Project root directory")

    # ── status ────────────────────────────────────────────────────────────────
    _  = subparsers.add_parser("status", help="Show past incident history")

    # ── config ────────────────────────────────────────────────────────────────
    __ = subparsers.add_parser("config", help="Show current configuration")

    # ── Parse & configure logger ──────────────────────────────────────────────
    args = parser.parse_args()
    _apply_global_flags(args)

    if args.command is None:
        parser.print_help()
        return

    # Build a runtime config (CLI flags override file config)
    config = get_config()
    if getattr(args, "auto_fix", None):
        config["auto_fix"] = True
    if getattr(args, "no_auto_fix", None):
        config["auto_fix"] = False
    if getattr(args, "auto_fix_threshold", None) is not None:
        config["auto_fix_threshold"] = args.auto_fix_threshold

    print("\n🛡️  LogGuard AI")
    print("=" * 40)
    print("Press Ctrl+C to exit at any time.\n")

    try:
        # ── run ───────────────────────────────────────────────────────────────
        if args.command == "run":
            from logguard.guard import run_guard
            sys.argv = [sys.argv[0], args.script] + args.args
            run_guard()

        # ── watch ─────────────────────────────────────────────────────────────
        elif args.command == "watch":
            from logguard.watcher import watch_logs
            watch_logs(args.logs, args.project)

        # ── analyze ───────────────────────────────────────────────────────────
        elif args.command == "analyze":
            _run_analyze(args, config)

        # ── status ────────────────────────────────────────────────────────────
        elif args.command == "status":
            _run_status()

        # ── config ────────────────────────────────────────────────────────────
        elif args.command == "config":
            _run_config(config)

    except KeyboardInterrupt:
        print("\n\nExiting…")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


# ── Sub-command implementations ───────────────────────────────────────────────

def _run_analyze(args, config: dict):
    """Handle the `analyze` sub-command."""
    from logguard.services.incident_manager import handle_incident

    target_path  = args.target or args.project
    logs_content = None
    log_path     = args.logs

    # Auto-discover common log filenames in the project root
    if not log_path and target_path and os.path.isdir(target_path):
        for candidate in ["app.log", "error.log", "server.log"]:
            p = os.path.join(target_path, candidate)
            if os.path.exists(p):
                log_path = p
                print(f"🔍 Auto-discovered log file: {log_path}")
                break

    if log_path:
        if os.path.exists(log_path):
            try:
                with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                    raw_logs = [
                        {"message": line.strip(), "level": "ERROR"}
                        for line in f.readlines()
                        if line.strip()
                    ]
                logs_content = truncate_logs(raw_logs)
                if len(logs_content) < len(raw_logs):
                    print(f"✂️  Logs truncated to last {len(logs_content)} lines (token limit)")
            except Exception as e:
                print(f"⚠️  Could not read log file '{log_path}': {e}")
        else:
            print(f"⚠️  Log file not found: '{log_path}'. Proceeding with code-only analysis.")
    else:
        print("ℹ️  No log file provided. Running static code analysis.")

    print(f"Triggering incident — service='{args.service}' severity='{args.severity}'")
    if target_path:
        print(f"Target: {target_path}\n")

    result = handle_incident(
        service=args.service,
        severity=args.severity,
        target_file_path=target_path,
        logs=logs_content,
        config=config,
    )

    print("\n✅ Incident handling complete.")
    if result:
        print(f"   Confidence:   {result.confidence:.0%}")
        print(f"   Fix applied:  {result.fix_applied}")


def _run_status():
    """Handle the `status` sub-command — show incident history table."""
    from logguard.utils.incident_log import get_all_incidents

    incidents = get_all_incidents()
    if not incidents:
        print("No incidents logged yet.")
        print(f"(Log file: {LOGGUARD_DIR / 'incidents.log'})")
        return

    # Show last 30 incidents, newest first
    shown = incidents[-30:][::-1]

    col_id   = 22
    col_svc  = 20
    col_sev  = 10
    col_conf = 11
    col_fix  = 12
    col_ts   = 20

    header = (
        f"{'INCIDENT ID':<{col_id}} "
        f"{'SERVICE':<{col_svc}} "
        f"{'SEVERITY':<{col_sev}} "
        f"{'CONFIDENCE':<{col_conf}} "
        f"{'FIX APPLIED':<{col_fix}} "
        f"{'TIMESTAMP':<{col_ts}}"
    )
    sep = "─" * len(header)

    print(f"\n{sep}")
    print(header)
    print(sep)
    for inc in shown:
        fix_marker = "✅ yes" if inc.get("fix_applied") else "  no"
        print(
            f"{inc.get('incident_id',''):<{col_id}} "
            f"{inc.get('service','')[:col_svc-1]:<{col_svc}} "
            f"{inc.get('severity',''):<{col_sev}} "
            f"{inc.get('confidence', 0):<{col_conf}.0%} "
            f"{fix_marker:<{col_fix}} "
            f"{inc.get('timestamp',''):<{col_ts}}"
        )
    print(f"{sep}\n")
    print(f"Total incidents: {len(incidents)}  |  Reports: {LOGGUARD_DIR / 'reports'}")


def _run_config(config: dict):
    """Handle the `config` sub-command — show current effective config."""
    print(f"\nConfig file: {CONFIG_FILE}")
    print(f"Log dir:     {LOGGUARD_DIR}\n")
    print("Effective settings:")
    col = max(len(k) for k in config) + 2
    for k, v in config.items():
        print(f"  {k:<{col}} {v}")
    print()


def _apply_global_flags(args=None):
    """Reconfigure the logger based on --verbose / --quiet flags or config."""
    from logguard.utils.logger import setup_logger
    from logguard.config import get_config

    level = get_config().get("log_level", "normal")
    if args is not None:
        if getattr(args, "verbose", False):
            level = "verbose"
        elif getattr(args, "quiet", False):
            level = "quiet"
    setup_logger(level=level)


if __name__ == "__main__":
    main()
