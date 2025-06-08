# src/app.py

from ui.gui import ModernUI
from core.listener import AssistantListener
from config.settings import load_settings
import threading

def main():
    """
    Main function to initialize and run the AI Virtual Assistant application.
    """
    settings = load_settings()
    assistant_name = settings.get('assistant_name', 'gemini')

    app = ModernUI()

    def on_wake_word():
        app.after(0, app.on_activation)

    listener = AssistantListener(assistant_name=assistant_name, callback=on_wake_word)
    listener.start()

    def on_closing():
        """
        Handles the application closing event.
        """
        print("Closing application...")
        listener.stop() 
        app.destroy()   

    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()

if __name__ == "__main__":
    main()