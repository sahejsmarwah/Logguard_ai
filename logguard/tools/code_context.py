"""
logguard/tools/code_context.py
-------------------------------
Reads source file context intelligently:
  - If an error_line is known, returns ±context_lines around it (with a >>> marker).
  - Falls back to the first 200 lines if no line number is available.
  - Always includes line numbers in output so the LLM can reference them precisely.
"""
import os


def get_code_context(
    file_path: str,
    error_line: int = None,
    context_lines: int = 80,
) -> str:
    """
    Read relevant portions of a source file.

    Args:
        file_path:     Absolute path to the source file.
        error_line:    The 1-indexed line number of the error (from stack trace).
        context_lines: How many lines before/after error_line to include.

    Returns:
        Formatted string with line numbers and an error-line marker (>>>).
    """
    if not os.path.exists(file_path):
        return f"[File not found: {file_path}]"

    try:
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        return f"[Could not read file: {e}]"

    total = len(lines)

    if error_line and 1 <= error_line <= total:
        start = max(0, error_line - context_lines - 1)
        end   = min(total, error_line + context_lines)
    else:
        start = 0
        end   = min(total, 200)

    numbered_lines = []
    for i, line in enumerate(lines[start:end], start=start + 1):
        marker = ">>>" if (error_line and i == error_line) else "   "
        numbered_lines.append(f"{marker} {i:5d} | {line}")

    header = f"# File: {file_path}"
    if error_line:
        header += f"  (error at line {error_line}, showing ±{context_lines} lines)"
    header += "\n"

    return header + "".join(numbered_lines)
