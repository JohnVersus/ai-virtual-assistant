from .gui import ModernUI
from .listener import AssistantListener
from .settings import load_settings
import threading

def main():
    settings = load_settings()
    assistant_name = settings.get('assistant_name', 'gemini')

    def on_wake_word():
        # This function needs to be thread-safe as it's called from the listener thread
        app.after(0, app.on_activation)

    listener = AssistantListener(assistant_name=assistant_name, callback=on_wake_word)
    listener.start()

    app = ModernUI(listener_callback=on_wake_word)

    def on_closing():
        print("Closing application...")
        listener.stop()
        app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_closing)
    app.mainloop()

if __name__ == "__main__":
    main()