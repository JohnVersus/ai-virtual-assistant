import speech_recognition as sr
import threading
import time
from queue import Queue

class AssistantListener:
    def __init__(self, assistant_name, callback):
        self.assistant_name = assistant_name.lower()
        self.callback = callback
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.stop_listening = None
        self.listening_thread = None

    def start(self):
        """Starts the background listening thread."""
        self.stop_listening = self.recognizer.listen_in_background(self.microphone, self._listen_for_wake_word, phrase_time_limit=5)
        print(f"Now listening in the background for '{self.assistant_name}'...")

    def stop(self):
        """Stops the background listening."""
        if self.stop_listening:
            self.stop_listening(wait_for_stop=False)
            print("Background listening stopped.")

    def _listen_for_wake_word(self, recognizer, audio):
        """Callback for the background listener."""
        try:
            text = recognizer.recognize_google(audio)
            print(f"Heard: {text}") # For debugging
            if self.assistant_name in text.lower():
                print(f"Activation word '{self.assistant_name}' detected!")
                self.callback()
        except sr.UnknownValueError:
            pass # Ignores phrases it can't understand
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")