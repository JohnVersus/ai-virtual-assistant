# src/ui/chat_gui.py
import tkinter as tk
from tkinter import scrolledtext, Toplevel, Label, Button, messagebox
import os # Added for path manipulation
import threading

# New SettingsModal class
class SettingsModal(Toplevel):
    def __init__(self, master, initial_settings_json_str: str, save_callback):
        super().__init__(master)
        self.title("Assistant Settings")
        self.geometry("600x500") 
        self.configure(bg='#1a1a1a')
        self.transient(master)  # Makes the modal appear on top of the main window
        self.grab_set()         # Disables interaction with the main window while modal is open
        self.save_callback = save_callback
        self.initial_settings_json_str = initial_settings_json_str # Store initial settings JSON string

        self._setup_ui() # Renamed to avoid conflict

        # Center the modal on the screen
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - (self.winfo_width() // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def _setup_ui(self):
        main_frame = tk.Frame(self, bg='#1a1a1a', padx=15, pady=15)
        main_frame.pack(expand=True, fill="both")

        info_label = Label(main_frame, text="Edit settings.json content directly:", bg='#1a1a1a', fg='#e0e0e0', font=("Helvetica", 10, "bold"))
        info_label.pack(pady=(0,5), anchor='w')

        self.settings_text_area = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            bg='#2a2a2a',
            fg='#e0e0e0',
            font=("Courier New", 10), # Monospaced font for JSON
            padx=10,
            pady=10,
            relief='flat',
            borderwidth=2,
            insertbackground='#e0e0e0' # Cursor color
        )
        self.settings_text_area.pack(expand=True, fill="both", pady=(0, 10))
        self.settings_text_area.insert(tk.END, self.initial_settings_json_str)

        # Save Button
        save_button = Button(main_frame, text="Save Settings", command=self._on_save_settings, bg='#4a4a4a', fg='#e0e0e0', relief='flat', activebackground='#5a5a5a', activeforeground='#e0e0e0')
        save_button.pack(pady=(5,0), anchor='e')

    def _on_save_settings(self):
        """Handles the save settings button click within the modal."""
        updated_settings_json_str = self.settings_text_area.get("1.0", tk.END).strip()
        
        # Basic JSON validation (optional but good)
        try:
            import json
            json.loads(updated_settings_json_str) # Try parsing
        except json.JSONDecodeError as e:
            messagebox.showerror("Invalid JSON", f"The settings content is not valid JSON.\nPlease correct it before saving.\n\nError: {e}")
            return

        if self.save_callback:
            # Run the callback in a separate thread to avoid freezing the UI
            threading.Thread(target=self.save_callback, args=(updated_settings_json_str,)).start()
        self.destroy() # Close the modal after saving

    def update_modal_content(self, new_settings_json_str: str):
        """Updates the text area in the modal with new settings JSON string."""
        self.initial_settings_json_str = new_settings_json_str
        self.settings_text_area.delete("1.0", tk.END)
        self.settings_text_area.insert(tk.END, self.initial_settings_json_str)


class ChatUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Virtual Assistant")
        self.geometry("500x650")
        self.configure(bg='#1a1a1a')
        
        self.save_settings_callback = None # To be set by the Application class
        self.current_settings_json_str_for_modal = "" # Will be populated by Application
        self.settings_modal = None # To hold the instance of the settings modal

        self.setup_ui()
        self.current_assistant_message_id = None

    def setup_ui(self):
        main_frame = tk.Frame(self, bg='#1a1a1a', padx=15, pady=15)
        main_frame.pack(expand=True, fill="both")

        # Chat display area
        self.chat_display = scrolledtext.ScrolledText(
            main_frame,
            wrap=tk.WORD,
            state='disabled',
            bg='#2a2a2a',
            fg='#e0e0e0',
            font=("Helvetica", 11),
            padx=10,
            pady=10,
            relief='flat',
            borderwidth=0
        )
        self.chat_display.pack(expand=True, fill="both", pady=(0, 15))
        
        # Configure tags for styling messages
        self.chat_display.tag_configure("user", foreground="#8ab4f8", justify='right', rmargin=10)
        self.chat_display.tag_configure("assistant", foreground="#97e5a4", justify='left', lmargin1=10, lmargin2=10)
        self.chat_display.tag_configure("status", foreground="#cccccc", justify='center', font=("Helvetica", 9, "italic"))

        # Status label
        self.status_label = tk.Label(
            main_frame,
            text="Initializing...",
            font=("Helvetica", 10),
            fg='#999999',
            bg='#1a1a1a'
        )
        self.status_label.pack(fill='x', pady=(5,0))

        # Settings Button
        settings_button = Button(
            main_frame,
            text="Settings",
            command=self.open_settings_modal,
            bg='#3a3a3a',
            fg='#e0e0e0',
            relief='flat',
            activebackground='#4a4a4a',
            activeforeground='#e0e0e0'
        )
        settings_button.pack(fill='x', pady=(10,0))


    def _insert_message(self, text, tags):
        """Helper to insert text and ensure view scrolls to the end."""
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, text, tags)
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)

    def add_message(self, sender: str, message: str):
        """Adds a complete message to the chat display."""
        header = f"{sender}\n"
        self._insert_message(header, ("user" if sender.lower() == "you" else "assistant",))
        self._insert_message(f"{message}\n\n", ("user" if sender.lower() == "you" else "assistant",))

    def start_assistant_message(self):
        """Prepares the UI for a new assistant message."""
        self._insert_message("Assistant\n", ("assistant",))
        # Mark the start of the content to be updated
        self.start_pos = self.chat_display.index(f"{tk.END}-1c")

    def update_assistant_message(self, chunk: str):
        """Appends a chunk of text to the current assistant message."""
        self.chat_display.config(state='normal')
        self.chat_display.insert(tk.END, chunk)
        self.chat_display.config(state='disabled')
        self.chat_display.see(tk.END)
        self.update_idletasks()

    def end_assistant_message(self):
        """Finalizes the assistant's message with spacing."""
        self._insert_message("\n\n", ())

    def set_status(self, text: str):
        """Updates the status bar text."""
        self.status_label.config(text=text)

    def update_settings_json_for_modal(self, settings_json_str: str):
        """Stores the current settings JSON string to be passed to the settings modal."""
        self.current_settings_json_str_for_modal = settings_json_str
        if self.settings_modal and self.settings_modal.winfo_exists(): # If modal already exists, update its field
            self.settings_modal.update_modal_content(self.current_settings_json_str_for_modal)

    def open_settings_modal(self):
        """Opens the settings modal window."""
        if not self.settings_modal or not self.settings_modal.winfo_exists():
            self.settings_modal = SettingsModal(
                self, 
                initial_settings_json_str=self.current_settings_json_str_for_modal,
                save_callback=self.save_settings_callback
            )
        else:
            self.settings_modal.deiconify() # If minimized, restore it
        self.settings_modal.grab_set() # Ensure modal is focused
        self.wait_window(self.settings_modal) # Wait for the modal to close
