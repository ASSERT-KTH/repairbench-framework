from dotenv import load_dotenv
import os
from pathlib import Path


def init_environment():
    """
    Initialize the environment by loading the .env file.
    This function can be called multiple times safely.
    """
    # Find the .env file in the project root
    # Start from the current file and work up to find the project root
    current_path = Path(__file__).resolve()
    project_root = None

    # Look for the project root by finding the directory that contains main scripts
    for parent in current_path.parents:
        if (parent / "generate_patches.py").exists() or (parent / ".env").exists():
            project_root = parent
            break

    if project_root and (project_root / ".env").exists():
        load_dotenv(project_root / ".env")
    else:
        # Fallback: just load from current working directory
        load_dotenv()


# Initialize environment when this module is imported
init_environment()
