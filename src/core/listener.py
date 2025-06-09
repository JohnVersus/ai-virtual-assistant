# src/core/listener.py
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

        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)

    def start(self):
        self.stop_listening = self.recognizer.listen_in_background(self.microphone, self._listen_for_wake_word, phrase_time_limit=5)
        print(f"Now listening in the background for '{self.assistant_name}'...")

    def stop(self):
        if self.stop_listening:
            self.stop_listening(wait_for_stop=False)
            print("Background listening stopped.")

    def _listen_for_wake_word(self, recognizer, audio):
        try:
            text = recognizer.recognize_google(audio)
            print(f"Heard: {text}") 
            if self.assistant_name in text.lower():
                print(f"Activation word '{self.assistant_name}' detected!")
                self.callback()
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")

    def listen_and_transcribe(self):
        print("Listening for a command...")
        try:
            with self.microphone as source:
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            text = self.recognizer.recognize_google(audio)
            print(f"Command transcribed: '{text}'")
            return text
        except sr.WaitTimeoutError:
            print("No command heard.")
            return None
        except sr.UnknownValueError:
            print("Could not understand the command.")
            return None
        except sr.RequestError as e:
            print(f"Speech recognition request failed: {e}")
            return None