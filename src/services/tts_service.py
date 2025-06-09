# src/services/tts_service.py
from elevenlabs.client import ElevenLabs
from elevenlabs import play
from ..config.settings import load_settings

def speak(text: str):
    try:
        settings = load_settings()
        api_key = settings.get('ELEVENLABS_API_KEY')
        voice_id = settings.get('ELEVENLABS_VOICE_ID')

        if not api_key:
            raise ValueError("ELEVENLABS_API_KEY not found.")
        
        if not voice_id:
            raise ValueError("ELEVENLABS_VOICE_ID not found in settings.")

        client = ElevenLabs(api_key=api_key)
        
        audio = client.generate(text=text, voice=voice_id)
        
        play(audio)

    except Exception as e:
        print(f"An error occurred while generating speech: {e}")

if __name__ == '__main__':
    # For direct testing of this module
    test_text = "Hello! This is a test of the text to speech service."
    print(f"Testing ElevenLabs TTS with text: '{test_text}'")
    speak(test_text)