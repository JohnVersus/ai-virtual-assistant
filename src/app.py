# src/app.py
import asyncio
import re
import threading
import time
import os
import wave
import pyaudio
from pynput import keyboard

from .ui.chat_gui import ChatUI
from .core.listener import AssistantListener
from .core.dspy_handler import DspyHandler
from .config.settings import load_settings, save_settings

class Application:
    def __init__(self, root):
        self.root = root
        self.settings = load_settings()
        self.assistant_name = self.settings.get('assistant_name', 'gemini')

        self.dspy_handler = DspyHandler()
        self.listener = AssistantListener(assistant_name=self.assistant_name, callback=self.on_wake_word_detected)

        self.conversation_history = []
        self.is_in_conversation_mode = False
        self.wait_timer = None
        self.activation_key_pressed_time = None
        self.activation_timer = None # To hold the timer for delayed activation

        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.run_async_loop, daemon=True)
        self.thread.start()

        # --- Keyboard Listener Setup ---
        self.keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release
        )
        self.keyboard_listener.start() 

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.listener.start()
        self.root.set_status(f"Listening for '{self.assistant_name}'...")
        
        # --- UI Settings Integration ---
        self.root.set_initial_assistant_name_for_modal(self.assistant_name)
        self.root.save_settings_callback = self._on_save_settings_from_ui

        # Initialize PyAudio for sound playback
        self.pyaudio_instance = pyaudio.PyAudio()


    def run_async_loop(self):
        """Runs the asyncio event loop in a separate thread."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def play_notification_sound(self):
        """Plays a short notification sound from a WAV file."""
        # Adjust path as necessary. Assuming 'res' folder is in the project root.
        script_dir = os.path.dirname(__file__)
        project_root = os.path.abspath(os.path.join(script_dir, '..', '..'))
        sound_file_path = os.path.join(project_root, 'res', 'notification.wav')
        
        if not os.path.exists(sound_file_path):
            print(f"Warning: Notification sound file not found at {sound_file_path}")
            return

        try:
            with wave.open(sound_file_path, 'rb') as wf:
                stream = self.pyaudio_instance.open(
                    format=self.pyaudio_instance.get_format_from_width(wf.getsampwidth()),
                    channels=wf.getnchannels(),
                    rate=wf.getframerate(),
                    output=True
                )
                
                # Read data in chunks and play
                chunk_size = 1024
                data = wf.readframes(chunk_size)
                while data:
                    stream.write(data)
                    data = wf.readframes(chunk_size)
                
                stream.stop_stream()
                stream.close()
                # Do NOT terminate pyaudio_instance here, as it's used by listener too.
                # It will be terminated on app close.

        except Exception as e:
            print(f"Error playing notification sound: {e}")


    def cancel_wait_timer(self):
        """Cancels the existing auto-sleep timer."""
        if self.wait_timer:
            self.wait_timer.cancel()
            self.wait_timer = None

    def start_wait_timer(self):
        """Starts a 15-second timer to exit conversation mode."""
        self.cancel_wait_timer()
        def _exit_mode():
            if self.is_in_conversation_mode:
                print("Conversation timeout. Exiting conversation mode.")
                self.is_in_conversation_mode = False
        
        self.wait_timer = threading.Timer(15.0, _exit_mode)
        self.wait_timer.start()

    def _activate_on_hold(self):
        """Activates the assistant if the key is still held after the delay."""
        if self.activation_key_pressed_time and not self.is_in_conversation_mode:
            held_duration = time.time() - self.activation_key_pressed_time
            if held_duration >= 2.0: # Double check duration
                print(f"A key held for 2 seconds. Activating assistant via shortcut.")
                self.root.after(0, self.on_keyboard_shortcut_detected)
                self.play_notification_sound() # Play sound on activation

    def _on_key_press(self, key):
        """Handles key press events for the global keyboard listener."""
        try:
            if isinstance(key, keyboard.KeyCode) and key.char == 'a': 
                if not self.activation_key_pressed_time:
                    self.activation_key_pressed_time = time.time()
                    print(f"'a' key pressed at {self.activation_key_pressed_time}") # Debug log
                    
                    # Start a timer to check for activation after 2 seconds
                    self.activation_timer = threading.Timer(2.0, self._activate_on_hold)
                    self.activation_timer.start()

            elif isinstance(key, keyboard.Key):
                 print(f"Special key pressed: {key}") 
        except AttributeError:
            print(f"Key without char attribute pressed: {key}")
            pass

    def _on_key_release(self, key):
        """Handles key release events for the global keyboard listener."""
        print(f"Key released: {key}") # Debug log for any key release
        try:
            if isinstance(key, keyboard.KeyCode) and key.char == 'a':
                # Cancel the activation timer if the key is released before 2 seconds
                if self.activation_timer and self.activation_timer.is_alive():
                    self.activation_timer.cancel()
                    print("Activation timer cancelled (key released too soon).")
                
                self.activation_key_pressed_time = None # Reset the timer
            elif isinstance(key, keyboard.Key):
                print(f"Special key released: {key}")
        except AttributeError:
            print(f"Key without char attribute released: {key}")
            pass

    def on_keyboard_shortcut_detected(self):
        """Method called when the keyboard shortcut is detected."""
        if not self.is_in_conversation_mode:
            threading.Thread(target=self.run_conversation, daemon=True).start()
            # Sound is played in _activate_on_hold now, not here.

    def on_wake_word_detected(self):
        """Kicks off the conversation when the wake word is heard."""
        if not self.is_in_conversation_mode:
            threading.Thread(target=self.run_conversation, daemon=True).start()
            self.play_notification_sound() # Play sound on wake word detection too

    def run_conversation(self):
        """Manages a single, continuous conversation from start to finish."""
        self.is_in_conversation_mode = True
        self.listener.stop()
        print("Wake word detected. Starting conversation loop.")
        
        self.start_wait_timer()

        while self.is_in_conversation_mode:
            self.root.set_status("Listening...")
            command = self.listener.listen_and_transcribe()

            if command and self.is_in_conversation_mode:
                self.cancel_wait_timer()
                
                self.root.add_message("You", command)
                self.conversation_history.append({"role": "user", "content": command})
                
                streaming_done_event = threading.Event()
                asyncio.run_coroutine_threadsafe(
                    self.stream_response(streaming_done_event), self.loop
                )
                streaming_done_event.wait()
                
                if self.is_in_conversation_mode:
                    self.start_wait_timer()

        print("Exiting conversation loop.")
        self.cancel_wait_timer()
        self.listener.start()
        self.root.set_status(f"Listening for '{self.assistant_name}'...")

    async def stream_response(self, done_event: threading.Event):
        """Streams the LLM response to the UI and signals completion."""
        self.root.start_assistant_message()
        full_response = ""
        history_to_send = self.conversation_history[-10:]

        try:
            async for chunk in self.dspy_handler.get_streamed_response(history_to_send):
                full_response += chunk
                self.root.update_assistant_message(chunk)
            
            if not full_response.strip():
                try:
                    last_interaction = self.dspy_handler.lm.history[-1]
                    raw_content = last_interaction['response'].choices[0].message.content
                    match = re.search(r'\[\[ ## answer ## \]\](.*)\[\[ ## completed ## \]\]', raw_content, re.DOTALL)
                    if match:
                        fallback_answer = match.group(1).strip()
                        self.root.update_assistant_message(fallback_answer)
                        full_response = fallback_answer
                except Exception:
                    pass
            
            self.root.end_assistant_message()
            if full_response.strip():
                self.conversation_history.append({"role": "assistant", "content": full_response})
        except Exception as e:
            error_message = f"\n[Error: {e}]"
            print(f"Error streaming response: {e}")
            self.root.update_assistant_message(error_message)
            self.is_in_conversation_mode = False
        finally:
            done_event.set()

    def _on_save_settings_from_ui(self, new_assistant_name: str):
        """Callback to save settings from the UI."""
        old_assistant_name = self.assistant_name
        self.assistant_name = new_assistant_name
        
        self.settings['assistant_name'] = new_assistant_name
        save_settings(self.settings)

        if old_assistant_name != new_assistant_name:
            print(f"Assistant name changed from '{old_assistant_name}' to '{new_assistant_name}'. Restarting listener.")
            self.listener.stop() 
            self.listener = AssistantListener(assistant_name=self.assistant_name, callback=self.on_wake_word_detected)
            self.listener.start()
            self.root.set_status(f"Listening for '{self.assistant_name}'...")
        else:
            self.root.set_status(f"Listening for '{self.assistant_name}'...")
        print("Settings saved successfully.")
        self.root.set_initial_assistant_name_for_modal(self.assistant_name)

    def on_closing(self):
        """Handles application cleanup and shutdown."""
        print("Closing application...")
        self.is_in_conversation_mode = False
        self.cancel_wait_timer()
        self.listener.stop()
        
        if self.keyboard_listener and self.keyboard_listener.running:
            self.keyboard_listener.stop()
            print("Keyboard listener stopped.")

        # Properly terminate PyAudio instance
        if hasattr(self, 'pyaudio_instance') and self.pyaudio_instance:
            self.pyaudio_instance.terminate()
            print("PyAudio instance terminated.")

        self.loop.call_soon_threadsafe(self.loop.stop)
        self.root.destroy()

def main():
    root = ChatUI()
    app = Application(root)
    root.mainloop()

if __name__ == "__main__":
    main()