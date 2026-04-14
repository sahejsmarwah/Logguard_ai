"""
logguard/utils/file_finder.py
------------------------------
Locates the faulty Python source file from a stack trace.
Also extracts the specific error line number for a given file.
"""
import os
import re


def find_faulty_file(project_root: str, logs: list) -> str | None:
    """
    Analyze logs for Python stack traces and find the corresponding source file
    inside project_root.

    Returns the absolute path to the most-likely faulty file, or None.
    """
    log_text = "\n".join([l.get("message", "") for l in logs])

    # Extract all 'File "...", line N' references from the traceback
    matches = re.findall(r'File "([^"]+)", line \d+', log_text)

    # Walk from deepest frame upward, prefer files inside project_root
    for filename in reversed(matches):
        clean = filename.strip()

        # Check absolute path — must be inside project_root
        if os.path.isabs(clean) and os.path.exists(clean):
            if _is_subpath(clean, project_root):
                return os.path.abspath(clean)

        # Resolve relative path against project_root
        candidate = os.path.abspath(os.path.join(project_root, clean))
        if os.path.exists(candidate) and _is_subpath(candidate, project_root):
            return candidate

        # Fallback: recursive basename search inside project_root
        basename = os.path.basename(clean)
        found = _find_file_recursively(project_root, basename)
        if found:
            return found

    return None


def find_error_line(log_text: str, file_path: str) -> int | None:
    """
    Extract the line number referenced in a stack trace for a specific file.

    Args:
        log_text:  The raw stack trace / log text.
        file_path: Absolute path to the file we care about.

    Returns:
        The 1-indexed line number, or None if not found.
    """
    basename = re.escape(os.path.basename(file_path))
    # Match: File "...something/basename...", line N
    pattern = re.compile(
        r'File "[^"]*' + basename + r'[^"]*", line (\d+)',
        re.IGNORECASE,
    )
    matches = pattern.findall(log_text)
    if matches:
        # Return the last (deepest in the call stack) occurrence
        return int(matches[-1])
    return None


# ── Internal helpers ──────────────────────────────────────────────────────────

def _find_file_recursively(root: str, filename: str) -> str | None:
    """Walk root and return the first file matching filename."""
    for dirpath, dirnames, filenames in os.walk(root):
        # Skip hidden directories (e.g. .git, __pycache__, node_modules)
        dirnames[:] = [d for d in dirnames if not d.startswith(".") and d != "__pycache__"]
        if filename in filenames:
            return os.path.join(dirpath, filename)
    return None


def _is_subpath(path: str, parent: str) -> bool:
    """Return True if path is inside (or equal to) parent."""
    path   = os.path.abspath(path)
    parent = os.path.abspath(parent)
    return os.path.commonpath([parent, path]) == parent
