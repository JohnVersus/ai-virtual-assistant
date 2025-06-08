import json
import os

SETTINGS_FILE = os.path.expanduser("~/.ai_virtual_assistant_settings.json")

def save_settings(settings):
    """Saves the settings to a file."""
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f)

def load_settings():
    """Loads the settings from a file, or returns defaults."""
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return get_default_settings()
    else:
        return get_default_settings()

def get_default_settings():
    """Returns the default settings."""
    return {'assistant_name': 'gemini'}