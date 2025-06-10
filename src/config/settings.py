# src/config/settings.py
import json
import os

SETTINGS_FILE = os.path.expanduser("~/.ai_virtual_assistant_settings.json")

def save_settings_from_dict(settings_dict: dict):
    """Saves a dictionary of settings to the JSON file."""
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings_dict, f, indent=4)

def save_settings_from_string(settings_json_str: str):
    """Saves a JSON string to the settings file after parsing it."""
    settings_dict = json.loads(settings_json_str) # Assumes string is valid JSON
    save_settings_from_dict(settings_dict)

def load_settings():
    settings = get_default_settings()
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            try:
                file_settings = json.load(f)
                settings.update(file_settings)
            except json.JSONDecodeError:
                print(f"Warning: Could not decode JSON from {SETTINGS_FILE}. Using defaults.")
    
    if 'GOOGLE_API_KEY' not in settings or not settings['GOOGLE_API_KEY']:
        settings['GOOGLE_API_KEY'] = os.environ.get('GOOGLE_API_KEY')

    if 'ELEVENLABS_API_KEY' not in settings or not settings['ELEVENLABS_API_KEY']:
        settings['ELEVENLABS_API_KEY'] = os.environ.get('ELEVENLABS_API_KEY')
    
    # Ensure mcp_servers list exists and is a list
    if 'mcp_servers' not in settings or not isinstance(settings['mcp_servers'], list):
        settings['mcp_servers'] = [] # Default to an empty list

    return settings

def get_default_settings():
    return {
        'assistant_name': 'gemini',
        'GOOGLE_API_KEY': None,
        'ELEVENLABS_API_KEY': None, # Default voice: "Rachel"
        'ELEVENLABS_VOICE_ID': '21m00Tcm4TlvDq8ikWAM',
        'mcp_servers': [
            {
                "id": "local_computer_control", # Unique identifier for this server config
                "type": "stdio", # "stdio" (for local scripts/commands) or "http" (future)
                "enabled": True, # Whether this server config should be used
                "description": "Default local server for basic computer control.",
                # For stdio type:
                "command": "python", # The command to run (e.g., "python", "npx")
                "args": ["src/core/mcp_tools_server.py"], # Arguments for the command
                "env": None, # Optional environment variables as a dict: {"VAR": "value"}
                # For http type (conceptual for future):
                # "base_url": "http://example.com/mcp_api",
                # "auth_token": "your_api_key_if_needed"
            }
        ]
    }