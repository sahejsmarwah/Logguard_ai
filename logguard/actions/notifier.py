"""
logguard/actions/notifier.py
-----------------------------
Desktop / terminal notification when an incident is detected or a fix is applied.
Uses `plyer` for OS-level toast notifications, with a graceful console fallback.
"""
import logging

logger = logging.getLogger("logguard")


def send_notification(title: str, message: str):
    """
    Send a desktop notification via plyer (Windows/macOS/Linux).
    Falls back to a highlighted console print if plyer is not installed
    or the platform doesn't support it.

    Args:
        title:   Short notification heading.
        message: Body text (keep under ~200 chars for readability).
    """
    try:
        from plyer import notification
        notification.notify(
            title=title,
            message=message,
            app_name="LogGuard AI",
            timeout=8,
        )
        logger.debug(f"🔔 Notification sent: {title}")
    except Exception as exc:
        # Fallback: prominent console banner
        border = "─" * 60
        logger.warning(f"\n{border}")
        logger.warning(f"🔔  {title}")
        logger.warning(f"   {message}")
        logger.warning(border)
