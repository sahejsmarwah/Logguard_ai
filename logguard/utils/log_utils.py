def truncate_logs(logs: list, max_lines: int = 150) -> list:
    """
    Truncates a list of log entries to the last N lines.
    This helps keep the total token count within LLM limits.
    """
    if not logs:
        return []
    
    if len(logs) <= max_lines:
        return logs
        
    return logs[-max_lines:]
