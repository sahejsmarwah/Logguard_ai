def get_code_context(file_path: str, start: int = 1, end: int = 200):
    try:
        with open(file_path, "r") as f:
            lines = f.readlines()
            return "".join(lines[start - 1 : end])
    except Exception as e:
        return f"Could not read file: {e}"
