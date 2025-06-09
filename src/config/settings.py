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

    return settings

def get_default_settings():
    return {
        'assistant_name': 'gemini',
        'GOOGLE_API_KEY': None,
        'ELEVENLABS_API_KEY': None,
        'ELEVENLABS_VOICE_ID': '21m00Tcm4TlvDq8ikWAM' # Default voice: "Rachel"
    }