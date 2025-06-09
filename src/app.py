# src/app.py
import threading
import time
from .ui.gui import ModernUI
from .core.listener import AssistantListener
from .config.settings import load_settings
import src.services.llm_service as llm
import src.services.tts_service as tts

def main():
    settings = load_settings()
    assistant_name = settings.get('assistant_name', 'gemini')

    app = ModernUI()
    
    # Timer for automatic return to wake word listening
    wait_timer = None
    conversation_mode = False
    
    def cancel_wait_timer():
        """Cancel the current wait timer if it exists"""
        nonlocal wait_timer
        if wait_timer:
            wait_timer.cancel()
            wait_timer = None
    
    def start_wait_timer():
        """Start a 15-second timer before returning to wake word listening"""
        nonlocal wait_timer, conversation_mode
        cancel_wait_timer()
        
        def return_to_wake_listening():
            nonlocal conversation_mode
            conversation_mode = False
            app.after(0, lambda: app.set_status(f"Listening for '{assistant_name}'", "listening"))
        
        wait_timer = threading.Timer(15.0, return_to_wake_listening)
        wait_timer.start()

    def handle_interaction():
        """This function runs on a separate thread to avoid deadlocks."""
        nonlocal conversation_mode
        
        # Only stop listener if we're not in conversation mode
        if not conversation_mode:
            listener.stop()
            time.sleep(1)

        app.after(0, lambda: app.set_status("Listening for command...", "listening"))
        command = listener.listen_and_transcribe()

        if command:
            app.after(0, lambda: app.set_status("Processing...", "thinking"))
            response_text = llm.get_response(command)

            if response_text:
                app.after(0, lambda: app.set_status("Speaking...", "speaking"))
                tts.speak(response_text)
                
                # Enter conversation mode and start listening immediately
                conversation_mode = True
                app.after(0, lambda: app.set_status("Listening... (15s auto-sleep)", "waiting"))
                
                # Start the continuous listening in conversation mode
                threading.Thread(target=continuous_listen, daemon=True).start()
                
                # Start timer for auto-return to wake word mode
                start_wait_timer()
            else:
                app.after(0, lambda: app.set_status("Sorry, couldn't process that", "listening"))
                if not conversation_mode:
                    listener.start()
        else:
            app.after(0, lambda: app.set_status("No command heard", "listening"))
            if not conversation_mode:
                listener.start()

    def continuous_listen():
        """Continuously listen for commands in conversation mode"""
        while conversation_mode:
            try:
                command = listener.listen_and_transcribe()
                if command and conversation_mode:
                    # Cancel the timer since user responded
                    cancel_wait_timer()
                    
                    app.after(0, lambda: app.set_status("Processing...", "thinking"))
                    response_text = llm.get_response(command)
                    
                    if response_text:
                        app.after(0, lambda: app.set_status("Speaking...", "speaking"))
                        tts.speak(response_text)
                        
                        if conversation_mode:  # Check if still in conversation mode
                            app.after(0, lambda: app.set_status("Listening... (15s auto-sleep)", "waiting"))
                            start_wait_timer()
                    else:
                        app.after(0, lambda: app.set_status("Sorry, couldn't process that", "waiting"))
                        if conversation_mode:
                            start_wait_timer()
                            
            except Exception as e:
                print(f"Error in continuous listen: {e}")
                time.sleep(0.5)

    def on_wake_word():
        """
        This callback runs on the listener thread.
        Cancel any existing timer and start interaction.
        """
        cancel_wait_timer()
        interaction_thread = threading.Thread(target=handle_interaction, daemon=True)
        interaction_thread.start()

    listener = AssistantListener(assistant_name=assistant_name, callback=on_wake_word)

    def on_closing():
        print("Closing application...")
        nonlocal conversation_mode
        conversation_mode = False
        cancel_wait_timer()
        listener.stop()
        app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_closing)

    listener.start()
    app.set_status(f"Listening for '{assistant_name}'", "listening")

    app.mainloop()

if __name__ == "__main__":
    main()