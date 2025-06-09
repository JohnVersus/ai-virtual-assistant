# src/app.py
import threading
from .ui.gui import ModernUI
from .core.listener import AssistantListener
from .config.settings import load_settings
import src.services.llm_service as llm
import src.services.tts_service as tts

def main():
    settings = load_settings()
    assistant_name = settings.get('assistant_name', 'gemini')

    app = ModernUI()
    
    def handle_interaction():
        app.after(0, lambda: app.set_status("Activated! Listening..."))
        
        command = listener.listen_and_transcribe()
        
        if command:
            app.after(0, lambda: app.set_status("Thinking..."))
            response_text = llm.get_response(command)
            
            if response_text:
                app.after(0, lambda: app.set_status("Speaking..."))
                tts.speak(response_text)
        else:
            app.after(0, lambda: app.set_status("No command heard."))

        app.after(2000, lambda: app.set_status(f"Listening for '{assistant_name}'"))


    def on_wake_word():
        interaction_thread = threading.Thread(target=handle_interaction)
        interaction_thread.start()

    listener = AssistantListener(assistant_name=assistant_name, callback=on_wake_word)
    
    def on_closing():
        print("Closing application...")
        listener.stop()
        app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_closing)
    
    # Start the listener only after the UI is ready
    listener.start()
    app.set_status(f"Listening for '{assistant_name}'")
    
    app.mainloop()

if __name__ == "__main__":
    main()