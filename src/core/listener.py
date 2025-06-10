# src/core/listener.py
import speech_recognition as sr

class AssistantListener:
    def __init__(self, assistant_name, callback):
        self.assistant_name = assistant_name.lower()
        self.callback = callback
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.stop_listening = None
        self.recognizer.pause_threshold = 2.0

        # Adjust for ambient noise once at the beginning
        with self.microphone as source:
            print("Calibrating microphone for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source)
            print("Calibration complete.")

    def start(self):
        """Starts listening in the background for the wake word."""
        if self.stop_listening is None: # Prevent starting multiple listeners
            self.stop_listening = self.recognizer.listen_in_background(
                self.microphone, self._listen_for_wake_word, phrase_time_limit=5
            )
            print(f"Now listening in the background for '{self.assistant_name}'...")

    def stop(self):
        """Stops the background listener and waits for it to terminate."""
        if self.stop_listening:
            # --- KEY FIX ---
            # wait_for_stop=True ensures the thread is stopped and the
            # microphone is released before this function returns.
            self.stop_listening(wait_for_stop=True)
            self.stop_listening = None # Mark as stopped
            print("Background listening has been confirmed to be stopped.")

    def _listen_for_wake_word(self, recognizer, audio):
        try:
            text = recognizer.recognize_google(audio)
            print(f"Heard: {text}")
            if self.assistant_name in text.lower():
                self.callback()
        except sr.UnknownValueError:
            pass # Ignore if speech is not understood
        except sr.RequestError as e:
            print(f"Could not request results from Google; {e}")

    def listen_and_transcribe(self):
        """Listens for a single command and transcribes it."""
        print("Listening for a command...")
        try:
            with self.microphone as source:
                # Removed phrase_time_limit to allow pause_threshold to dictate end of speech.
                # timeout=5 means it will wait 5s for speech to start.
                audio = self.recognizer.listen(source, timeout=5)

            text = self.recognizer.recognize_google(audio)
            print(f"Command transcribed: '{text}'")
            return text
        except sr.WaitTimeoutError:
            print("No command heard (timeout).")
            return None
        except sr.UnknownValueError:
            print("Could not understand the command.")
            return None
        except sr.RequestError as e:
            print(f"Speech recognition request failed: {e}")
            return None