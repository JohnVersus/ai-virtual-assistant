# src/ui/chat_gui.py
import tkinter as tk
from tkinter import scrolledtext

class ChatUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Virtual Assistant")
        self.geometry("500x650")
        self.configure(bg='#1a1a1a')
        
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
        self.status_label.pack(fill='x')

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
        
        self.current_assistant_message_id = self.chat_display.index(tk.END)
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