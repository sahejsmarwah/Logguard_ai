"""
logguard/config.py
------------------
Manages user configuration for LogGuard AI.
Config lives at ~/.logguard/config.yaml and is merged with defaults on load.
"""
import os
from pathlib import Path

LOGGUARD_DIR = Path.home() / ".logguard"
CONFIG_FILE = LOGGUARD_DIR / "config.yaml"

DEFAULTS = {
    # Set to True to let LogGuard apply fixes automatically above the threshold.
    "auto_fix": False,
    # Minimum confidence (0.0–1.0) required to trigger auto-fix.
    "auto_fix_threshold": 0.85,
    # Content-based deduplication for the watcher (same error block → skip).
    "watcher_dedup": True,
    # Logging verbosity: "normal", "verbose", or "quiet"
    "log_level": "normal",
}


def get_config() -> dict:
    """
    Load config from ~/.logguard/config.yaml merged over DEFAULTS.
    Creates a default config file if none exists.
    """
    # Ensure config dir exists and write defaults on first run
    LOGGUARD_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        _write_default_config()

    config = dict(DEFAULTS)
    try:
        import yaml
        with open(CONFIG_FILE, "r") as f:
            user_config = yaml.safe_load(f) or {}
            config.update({k: v for k, v in user_config.items() if k in DEFAULTS})
    except ImportError:
        # PyYAML not installed — use defaults silently
        pass
    except Exception:
        pass

    return config


def _write_default_config():
    """Write a well-commented default config file."""
    content = """\
# LogGuard AI Configuration
# Location: ~/.logguard/config.yaml

# Auto-fix mode
# When true, LogGuard will apply fixes automatically if confidence >= auto_fix_threshold.
# When false, it always asks for human approval first (recommended for sensitive code).
auto_fix: false

# Confidence threshold for auto-fix (0.0 to 1.0).
# Only used when auto_fix is true.
auto_fix_threshold: 0.85

# Watcher deduplication
# When true, the log watcher ignores repeat occurrences of the exact same error block.
watcher_dedup: true

# Log verbosity: "normal", "verbose", or "quiet"
log_level: normal
"""
    with open(CONFIG_FILE, "w") as f:
        f.write(content)
