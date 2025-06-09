# src/app.py
import asyncio
import threading
import time
from .ui.chat_gui import ChatUI
from .core.listener import AssistantListener
from .core.dspy_handler import DspyHandler
from .config.settings import load_settings

class Application:
    def __init__(self, root):
        self.root = root
        self.settings = load_settings()
        self.assistant_name = self.settings.get('assistant_name', 'gemini')

        self.dspy_handler = DspyHandler()
        self.listener = AssistantListener(assistant_name=self.assistant_name, callback=self.on_wake_word)

        self.loop = asyncio.new_event_loop()
        self.thread = threading.Thread(target=self.run_async_loop, daemon=True)
        self.thread.start()

        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.listener.start()
        self.root.set_status(f"Listening for '{self.assistant_name}'...")

    def run_async_loop(self):
        """Runs the asyncio event loop in a separate thread."""
        asyncio.set_event_loop(self.loop)
        self.loop.run_forever()

    def on_wake_word(self):
        """Callback triggered when the wake word is detected."""
        # This function is called from the listener's thread.
        # We start command handling in a new thread to avoid blocking.
        threading.Thread(target=self.handle_command, daemon=True).start()

    def handle_command(self):
        """Stops background listening, transcribes a command, and processes it."""
        # --- FIX STARTS HERE ---
        # 1. Stop the background listener to free up the microphone.
        self.listener.stop()
        print("Wake word detected! Stopped background listening.")
        self.root.set_status("Listening for command...")
        
        # A brief pause can sometimes help ensure the resource is fully released.
        time.sleep(0.1) 
        
        # 2. Now, safely listen for and transcribe the command.
        command = self.listener.listen_and_transcribe()
        
        if command:
            self.root.set_status("Processing...")
            self.root.add_message("You", command)
            
            # 3. Schedule the async streaming task. The listener will be restarted there.
            asyncio.run_coroutine_threadsafe(self.stream_response(command), self.loop)
        else:
            self.root.set_status(f"No command heard. Restarting listener...")
            print("No command heard. Restarting background listener.")
            # 4. If no command, restart the background listener immediately.
            self.listener.start()
        # --- FIX ENDS HERE ---

    async def stream_response(self, command):
        """Streams the LLM response to the UI and restarts the listener."""
        self.root.start_assistant_message()
        try:
            async for chunk in self.dspy_handler.get_streamed_response(command):
                self.root.update_assistant_message(chunk)
            self.root.end_assistant_message()
        except Exception as e:
            print(f"Error streaming response: {e}")
            self.root.update_assistant_message(f"\n[Error: {e}]")
        finally:
            self.root.set_status(f"Done. Listening for '{self.assistant_name}'...")
            print("Response finished. Restarting background listener.")
            # --- FIX ---
            # 5. Crucially, restart the background listener after processing is complete.
            self.listener.start()
            # --- END FIX ---

    def on_closing(self):
        """Handles application cleanup and shutdown."""
        print("Closing application...")
        self.listener.stop()
        self.loop.call_soon_threadsafe(self.loop.stop)
        # self.thread.join() # This can sometimes cause a hang on close, can be omitted.
        self.root.destroy()

def main():
    root = ChatUI()
    app = Application(root)
    root.mainloop()

if __name__ == "__main__":
    main()