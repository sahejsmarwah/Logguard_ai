"""
logguard/utils/logger.py
-------------------------
Colored terminal logger for LogGuard AI.
Uses ANSI escape codes — no extra dependencies.
"""
import logging
import sys

# ANSI color codes
RESET   = "\033[0m"
RED     = "\033[91m"
YELLOW  = "\033[93m"
GREEN   = "\033[92m"
CYAN    = "\033[96m"
BLUE    = "\033[94m"
BOLD    = "\033[1m"
DIM     = "\033[2m"


class _ColorFormatter(logging.Formatter):
    """Applies ANSI color to log messages based on level."""

    LEVEL_COLORS = {
        logging.DEBUG:    BLUE,
        logging.INFO:     GREEN,
        logging.WARNING:  YELLOW,
        logging.ERROR:    RED,
        logging.CRITICAL: RED + BOLD,
    }

    def format(self, record):
        color = self.LEVEL_COLORS.get(record.levelno, RESET)
        # Color the time dim, message colored
        record.msg = f"{color}{record.msg}{RESET}"
        return super().format(record)


def setup_logger(level: str = "normal") -> logging.Logger:
    """
    Configure and return the LogGuard named logger.

    Args:
        level: "verbose" / "quiet" / "normal" (default)
    """
    logger = logging.getLogger("logguard")

    level_map = {
        "verbose": logging.DEBUG,
        "quiet":   logging.WARNING,
        "normal":  logging.INFO,
    }
    logger.setLevel(level_map.get(level, logging.INFO))

    handler = logging.StreamHandler(sys.stdout)
    formatter = _ColorFormatter(
        f"{DIM}[%(asctime)s]{RESET} %(message)s",
        datefmt="%H:%M:%S",
    )
    handler.setFormatter(formatter)

    # Avoid adding duplicate handlers if called multiple times
    logger.handlers = []
    logger.addHandler(handler)
    logger.propagate = False

    return logger
