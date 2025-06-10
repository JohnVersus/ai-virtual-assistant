# src/config/settings.py
import json
import os

SETTINGS_FILE = os.path.expanduser("~/.ai_virtual_assistant_settings.json")

def save_settings(settings):
    with open(SETTINGS_FILE, 'w') as f:
        json.dump(settings, f, indent=4)

def load_settings():
    settings = get_default_settings()
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, 'r') as f:
            try:
                file_settings = json.load(f)
                settings.update(file_settings)
            except json.JSONDecodeError:
                pass
    
    if 'GOOGLE_API_KEY' not in settings or not settings['GOOGLE_API_KEY']:
        settings['GOOGLE_API_KEY'] = os.environ.get('GOOGLE_API_KEY')

    if 'ELEVENLABS_API_KEY' not in settings or not settings['ELEVENLABS_API_KEY']:
        settings['ELEVENLABS_API_KEY'] = os.environ.get('ELEVENLABS_API_KEY')

    # Ensure MCP server settings have defaults if not present
    settings.setdefault('mcp_use_external_python_server', False) # User choice from UI
    settings.setdefault('mcp_external_python_script_path', '') # Path to user's python MCP script

    settings.setdefault('mcp_server_type', 'local') # For advanced config: 'local' or 'external'
    settings.setdefault('mcp_external_command', None) # For advanced config
    settings.setdefault('mcp_external_args', [])    # For advanced config
    settings.setdefault('mcp_external_env', None)   # Optional environment variables for the external server

    return settings

def get_default_settings():
    return {
        'assistant_name': 'gemini',
        'GOOGLE_API_KEY': None,
        'ELEVENLABS_API_KEY': None, # Default voice: "Rachel"
        'ELEVENLABS_VOICE_ID': '21m00Tcm4TlvDq8ikWAM',
        'mcp_use_external_python_server': False,
        'mcp_external_python_script_path': '',
        'mcp_server_type': 'local', # Fallback/advanced
        'mcp_external_command': None, # Fallback/advanced
        'mcp_external_args': [], # Fallback/advanced
        'mcp_external_env': None, # Fallback/advanced
    }