import os
import json
from pathlib import Path

# Create a deterministic app directory in the user's home folder
APP_DIR = Path.home() / ".mg400ai"

DEFAULT_CONFIG = {
    "gemini_api_key": "",
    "last_template_path": "",
    "pusher_app_id": "",
    "pusher_secret": "",
    "pusher_cluster": "ap2",
    "log_level": "INFO"
}

class ConfigManager:
    """Manages reading and writing application settings to a persistent config.json file."""
    def __init__(self):
        self.config_path = APP_DIR / "config.json"
        self.config = DEFAULT_CONFIG.copy()
        self._ensure_app_dir()
        self.load()

    def _ensure_app_dir(self):
        try:
            APP_DIR.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            print(f"Warning: Could not create config directory {APP_DIR}: {e}")

    def load(self):
        if self.config_path.exists():
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Update config with whatever fields were parsed cleanly
                    for k, v in data.items():
                        self.config[k] = v
            except Exception as e:
                print(f"Warning: Config file corrupted or unreadable. Falling back to defaults. ({e})")
        else:
            self.save()

    def save(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Warning: Failed to save config file: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()
