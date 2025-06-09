# src/app.py
import asyncio
import re
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

        self.dspy_handler = DspyHandler()
        self.listener = AssistantListener(assistant_name=self.assistant_name, callback=self.on_wake_word_detected)

        self.conversation_history = []
        self.is_in_conversation_mode = False
        self.wait_timer = None

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
        def _exit_mode():
            if self.is_in_conversation_mode:
                print("Conversation timeout. Exiting conversation mode.")
                self.is_in_conversation_mode = False
        
        self.wait_timer = threading.Timer(15.0, _exit_mode)
        self.wait_timer.start()

    def on_wake_word_detected(self):
        """Kicks off the conversation when the wake word is heard."""
        if not self.is_in_conversation_mode:
            threading.Thread(target=self.run_conversation, daemon=True).start()

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
                
                self.root.set_status("Processing...")
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
            
            # If streaming produced an empty response, silently try to recover it.
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
                    # If fallback fails, do so silently. The user will see no response.
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