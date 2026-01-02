import os
import re

def find_faulty_file(project_root: str, logs: list) -> str:
    """
    Analyzes logs for stack traces and finds the corresponding file in the project.
    Returns the absolute path to the most likely faulty file, or None.
    """
    # 1. Extract all filenames from stack traces
    # Regex to catch "File "path/to/file.py", line N"
    candidates = []
    
    # Flatten logs to a single string for easier regex
    log_text = "\n".join([l.get("message", "") for l in logs])
    
    # Pattern for Python stack traces
    matches = re.findall(r'File "(.*?)", line \d+', log_text)
    
    # Reverse to find the "deepest" or most recent user code (ignoring libraries if possible)
    # Heuristic: We prefer files that actually exist inside our project root.
    for filename in reversed(matches):
        # Clean up path
        clean_name = filename.strip()
        
        # Check if it exists as absolute path
        if os.path.exists(clean_name):
             # Ensure it's inside the project root to avoid patching system libs
             if _is_subpath(clean_name, project_root):
                 return os.path.abspath(clean_name)
                 
        # If it's relative, try to resolve it against project root
        candidate_abs = os.path.abspath(os.path.join(project_root, clean_name))
        if os.path.exists(candidate_abs) and _is_subpath(candidate_abs, project_root):
            return candidate_abs
            
        # Recursive search: filename might be just "services/payment.py" 
        # but safely finding it in valid subdirs might be expensive. 
        # For now, let's stick to direct matches or relative matches.
        
        # Fallback: Check if the filename defines a unique file in the project
        # e.g. "payment.py" inside project_root
        basename = os.path.basename(clean_name)
        found_recursive = _find_file_recursively(project_root, basename)
        if found_recursive:
            return found_recursive

    return None

def _find_file_recursively(root, filename):
    for dirpath, dirnames, filenames in os.walk(root):
        if filename in filenames:
            return os.path.join(dirpath, filename)
    return None

def _is_subpath(path, parent):
    path = os.path.abspath(path)
    parent = os.path.abspath(parent)
    return os.path.commonpath([parent, path]) == parent
