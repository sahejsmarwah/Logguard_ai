import shutil
import os

def apply_patch(file_path: str, patch_content: str, backup: bool = True):
    """
    Simulates applying a patch by rewriting the file content.
    Refined to actually replace content if simple string match, or overwrite for MVP.
    For this MVP, we will assume the patch_content IS the new content 
    or we can implement a simple text replacement if provided in a diff format.
    
    To keep it reliable for the agent, we'll assume the agent provides the FULL new content 
    for the file in 'patch_content' for now, or we can use a library if we want real diff patching.
    
    Let's go with: 'patch_content' is the WHOLE new file content.
    """
    if not os.path.exists(file_path):
        return {"success": False, "error": f"File not found: {file_path}"}

    if backup:
        shutil.copy(file_path, f"{file_path}.bak")

    try:
        with open(file_path, "w") as f:
            f.write(patch_content)
        return {"success": True, "message": f"Applied patch to {file_path}"}
    except Exception as e:
        return {"success": False, "error": f"Failed to apply patch: {str(e)}"}

def restore_backup(file_path: str):
    if os.path.exists(f"{file_path}.bak"):
        shutil.copy(f"{file_path}.bak", file_path)
        os.remove(f"{file_path}.bak")
        return {"success": True, "message": "Restored backup"}
    return {"success": False, "message": "No backup found"}
