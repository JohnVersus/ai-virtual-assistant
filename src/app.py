# src/app.py
import asyncio
import threading
from .ui.chat_gui import ChatUI
from .core.listener import AssistantListener
from .core.dspy_handler import DspyHandler
from .config.settings import load_settings

class Application:
    def __init__(self, root):
        self.root = root
        self.settings = load_settings()
        self.assistant_name = self.settings.get('assistant_name', 'gemini')

        # Core components
        self.dspy_handler = DspyHandler()
        self.listener = AssistantListener(assistant_name=self.assistant_name, callback=self.on_wake_word_detected)

        # State and history management
        self.conversation_history = []
        self.is_in_conversation_mode = False
        self.wait_timer = None

        # Async loop for streaming
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

    def cancel_wait_timer(self):
        """Cancels the existing auto-sleep timer."""
        if self.wait_timer:
            self.wait_timer.cancel()
            self.wait_timer = None

    def start_wait_timer(self):
        """Starts a 15-second timer to exit conversation mode."""
        self.cancel_wait_timer()
        
        def exit_conversation_mode():
            print("Conversation timeout. Exiting conversation mode.")
            self.is_in_conversation_mode = False
        
        self.wait_timer = threading.Timer(15.0, exit_conversation_mode)
        self.wait_timer.start()

    def on_wake_word_detected(self):
        """Starts the initial interaction when the wake word is heard."""
        if self.is_in_conversation_mode:
            return

        # Stop any lingering timers and start the interaction in a new thread
        self.cancel_wait_timer()
        threading.Thread(target=self.handle_first_interaction, daemon=True).start()

    def handle_first_interaction(self):
        """Handles the first command after the wake word."""
        self.listener.stop()
        
        command = self.process_command() # Get and process one command
        
        if command:
            # If a command was successfully processed, enter continuous conversation mode
            self.is_in_conversation_mode = True
            threading.Thread(target=self.continuous_listen, daemon=True).start()
        else:
            # If no command, go back to wake word listening
            self.is_in_conversation_mode = False
            self.listener.start()
            self.root.set_status(f"Listening for '{self.assistant_name}'...")

    def continuous_listen(self):
        """Listens continuously for commands while in conversation mode."""
        print("Entered continuous conversation mode.")
        self.start_wait_timer() # Start the 15s timer

        while self.is_in_conversation_mode:
            command = self.process_command()
            if command:
                # If the user speaks, reset the auto-sleep timer
                self.start_wait_timer()
        
        # Loop has ended (either by timeout or error), so revert to wake word listening
        print("Exited continuous conversation mode.")
        self.cancel_wait_timer()
        self.listener.start()
        self.root.set_status(f"Listening for '{self.assistant_name}'...")

    def process_command(self):
        """Shared logic to listen, transcribe, and process a single command."""
        self.root.set_status("Listening...")
        command = self.listener.listen_and_transcribe()

        if command:
            self.root.set_status("Processing...")
            self.root.add_message("You", command)
            self.conversation_history.append({"role": "user", "content": command})
            
            streaming_done_event = threading.Event()
            asyncio.run_coroutine_threadsafe(
                self.stream_response(streaming_done_event), self.loop
            )
            streaming_done_event.wait()
        
        return command

    async def stream_response(self, done_event: threading.Event):
        """Streams the LLM response to the UI."""
        self.root.start_assistant_message()
        full_response = ""
        history_to_send = self.conversation_history[-10:]

        try:
            async for chunk in self.dspy_handler.get_streamed_response(history_to_send):
                full_response += chunk
                self.root.update_assistant_message(chunk)
            
            self.root.end_assistant_message()
            if full_response.strip():
                self.conversation_history.append({"role": "assistant", "content": full_response})
        except Exception as e:
            error_message = f"\n[Error: {e}]"
            print(f"Error streaming response: {e}")
            self.root.update_assistant_message(error_message)
        finally:
            done_event.set()

    def on_closing(self):
        """Handles application cleanup and shutdown."""
        print("Closing application...")
        self.is_in_conversation_mode = False
        self.cancel_wait_timer()
        self.listener.stop()
        self.loop.call_soon_threadsafe(self.loop.stop)
        self.root.destroy()

def main():
    root = ChatUI()
    app = Application(root)
    root.mainloop()

if __name__ == "__main__":
    main()