# auth_manager.py
import os
import json
from pathlib import Path

CONFIG_DIR = Path.home() / ".httpayer"
CONFIG_PATH = CONFIG_DIR / "config.json"

def save_api_key(api_key: str):
    """
    Save the API key securely in ~/.httpayer/config.json
    """
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump({"api_key": api_key}, f)
    # Restrict permissions: read/write only for the user
    try:
        os.chmod(CONFIG_PATH, 0o600)
    except PermissionError:
        pass  # may not work on all OS/filesystems

def load_api_key() -> str | None:
    """
    Load the API key from ~/.httpayer/config.json or environment
    """
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH) as f:
            return json.load(f).get("api_key")
    # fallback to environment
    return os.getenv("HTTPAYER_API_KEY")

def clear_api_key():
    """
    Delete the saved API key (logout functionality)
    """
    if CONFIG_PATH.exists():
        CONFIG_PATH.unlink()
