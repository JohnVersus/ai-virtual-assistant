import tkinter as tk
from tkinter import ttk, messagebox
from ..config.settings import save_settings, load_settings

class ModernUI(tk.Tk):
    def __init__(self, listener_callback):
        super().__init__()
        self.title("AI Virtual Assistant")
        self.geometry("350x200")
        self.listener_callback = listener_callback

        self.settings = load_settings()

        # Style
        style = ttk.Style(self)
        style.theme_use('aqua') # 'aqua' is a modern theme on macOS
        style.configure("TLabel", padding=10, font=("Helvetica", 14))
        style.configure("TButton", padding=10, font=("Helvetica", 12))

        # Main frame
        main_frame = ttk.Frame(self, padding="20")
        main_frame.pack(expand=True, fill="both")

        self.status_label = ttk.Label(main_frame, text="Status: Listening...", anchor="center")
        self.status_label.pack(pady=10)

        settings_button = ttk.Button(main_frame, text="Settings", command=self.open_settings)
        settings_button.pack(pady=10)

    def open_settings(self):
        settings_window = tk.Toplevel(self)
        settings_window.title("Settings")
        settings_window.geometry("300x150")

        settings_frame = ttk.Frame(settings_window, padding="20")
        settings_frame.pack(expand=True, fill="both")

        ttk.Label(settings_frame, text="Assistant Name:").pack(pady=5)
        
        self.name_entry = ttk.Entry(settings_frame, font=("Helvetica", 12))
        self.name_entry.insert(0, self.settings.get('assistant_name', 'gemini'))
        self.name_entry.pack(pady=5)

        save_button = ttk.Button(settings_frame, text="Save", command=lambda: self.save_assistant_name(settings_window))
        save_button.pack(pady=10)

    def save_assistant_name(self, window):
        new_name = self.name_entry.get().strip()
        if new_name:
            self.settings['assistant_name'] = new_name
            save_settings(self.settings)
            messagebox.showinfo("Settings Saved", "Assistant name updated. Please restart the app for changes to take effect.")
            window.destroy()
        else:
            messagebox.showwarning("Invalid Name", "Assistant name cannot be empty.")

    def on_activation(self):
        # This function is called when the wake word is detected
        self.status_label.config(text="Status: Activated!")
        # Add logic here to interact with the assistant
        print("UI has been notified of activation.")
        # Reset status after a delay
        self.after(2000, lambda: self.status_label.config(text="Status: Listening..."))