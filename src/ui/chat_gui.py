# src/ui/chat_gui.py
import tkinter as tk
from tkinter import scrolledtext, Toplevel, Label, Entry, Button, Checkbutton, StringVar, BooleanVar, filedialog
import os # Added for path manipulation
import threading

# New SettingsModal class
class SettingsModal(Toplevel):
    def __init__(self, master, initial_settings: dict, save_callback):
        super().__init__(master)
        self.title("Assistant Settings")
        self.geometry("450x300") 
        self.configure(bg='#1a1a1a')
        self.transient(master)  # Makes the modal appear on top of the main window
        self.grab_set()         # Disables interaction with the main window while modal is open

        self.save_callback = save_callback
        self.initial_settings = initial_settings # Store initial settings

        self.setup_ui()

        # Center the modal on the screen
        self.update_idletasks()
        x = master.winfo_x() + (master.winfo_width() // 2) - (self.winfo_width() // 2)
        y = master.winfo_y() + (master.winfo_height() // 2) - (self.winfo_height() // 2)
        self.geometry(f"+{x}+{y}")

    def setup_ui(self):
        main_frame = tk.Frame(self, bg='#1a1a1a', padx=15, pady=15)
        main_frame.pack(expand=True, fill="both")

        row_idx = 0

        # Assistant Name setting
        name_label = Label(main_frame, text="Assistant Name:", bg='#1a1a1a', fg='#e0e0e0', font=("Helvetica", 10))
        name_label.grid(row=row_idx, column=0, padx=5, pady=5, sticky='w')
        
        self.assistant_name_entry = Entry(main_frame, width=30, bg='#3a3a3a', fg='#e0e0e0', insertbackground='#e0e0e0', relief='flat')
        self.assistant_name_entry.insert(0, self.initial_settings.get('assistant_name', ''))
        self.assistant_name_entry.grid(row=row_idx, column=1, columnspan=2, padx=5, pady=5, sticky='ew')
        row_idx += 1

        # --- MCP Server Settings ---
        mcp_label = Label(main_frame, text="MCP Server Configuration:", bg='#1a1a1a', fg='#e0e0e0', font=("Helvetica", 10, "bold"))
        mcp_label.grid(row=row_idx, column=0, columnspan=3, padx=5, pady=(10,5), sticky='w')
        row_idx += 1

        self.mcp_use_external_var = BooleanVar(value=self.initial_settings.get('mcp_use_external_python_server', False))
        self.mcp_use_external_check = Checkbutton(
            main_frame, text="Use External Python MCP Server", variable=self.mcp_use_external_var,
            onvalue=True, offvalue=False, command=self.toggle_mcp_script_path_entry,
            bg='#1a1a1a', fg='#e0e0e0', selectcolor='#3a3a3a', activebackground='#1a1a1a', activeforeground='#e0e0e0',
            font=("Helvetica", 10)
        )
        self.mcp_use_external_check.grid(row=row_idx, column=0, columnspan=3, padx=5, pady=5, sticky='w')
        row_idx += 1

        mcp_script_path_label = Label(main_frame, text="External Script Path:", bg='#1a1a1a', fg='#e0e0e0', font=("Helvetica", 10))
        mcp_script_path_label.grid(row=row_idx, column=0, padx=5, pady=5, sticky='w')

        self.mcp_script_path_entry = Entry(main_frame, width=30, bg='#3a3a3a', fg='#e0e0e0', insertbackground='#e0e0e0', relief='flat')
        self.mcp_script_path_entry.insert(0, self.initial_settings.get('mcp_external_python_script_path', ''))
        self.mcp_script_path_entry.grid(row=row_idx, column=1, padx=5, pady=5, sticky='ew')

        browse_button = Button(main_frame, text="Browse", command=self.browse_mcp_script, bg='#4a4a4a', fg='#e0e0e0', relief='flat', activebackground='#5a5a5a', activeforeground='#e0e0e0')
        browse_button.grid(row=row_idx, column=2, padx=5, pady=5, sticky='e')
        row_idx += 1

        # Save Button
        save_button = Button(main_frame, text="Save Settings", command=self._on_save_settings, bg='#4a4a4a', fg='#e0e0e0', relief='flat', activebackground='#5a5a5a', activeforeground='#e0e0e0')
        save_button.grid(row=row_idx, column=1, columnspan=2, padx=5, pady=(15,5), sticky='e')

        main_frame.grid_columnconfigure(1, weight=1) # Allow entry fields to expand
        self.toggle_mcp_script_path_entry() # Set initial state of script path entry

    def toggle_mcp_script_path_entry(self):
        # Define a suggested default path for the external MCP script
        default_script_path = os.path.expanduser("~/.ai_virtual_assistant/mcp_server_external.py")

        if self.mcp_use_external_var.get():
            self.mcp_script_path_entry.config(state='normal')
            # If the "Use External" checkbox is ticked and the path entry is currently empty,
            # pre-fill it with the default suggested path.
            if not self.mcp_script_path_entry.get().strip():
                self.mcp_script_path_entry.delete(0, tk.END)
                self.mcp_script_path_entry.insert(0, default_script_path)
        else:
            self.mcp_script_path_entry.config(state='disabled')
    def browse_mcp_script(self):
        filepath = filedialog.askopenfilename(
            title="Select Python MCP Server Script",
            filetypes=(("Python files", "*.py"), ("All files", "*.*"))
        )
        if filepath:
            self.mcp_script_path_entry.delete(0, tk.END)
            self.mcp_script_path_entry.insert(0, filepath)

    def _on_save_settings(self):
        """Handles the save settings button click within the modal."""
        updated_settings = {
            'assistant_name': self.assistant_name_entry.get().strip(),
            'mcp_use_external_python_server': self.mcp_use_external_var.get(),
            'mcp_external_python_script_path': self.mcp_script_path_entry.get().strip() if self.mcp_use_external_var.get() else ''
        }
        if self.save_callback:
            # Run the callback in a separate thread to avoid freezing the UI
            threading.Thread(target=self.save_callback, args=(updated_settings,)).start()
        self.destroy() # Close the modal after saving

    def update_modal_fields(self, settings: dict):
        """Updates all fields in the modal with new settings values."""
        self.initial_settings = settings.copy() # Update stored initial settings
        self.assistant_name_entry.delete(0, tk.END)
        self.assistant_name_entry.insert(0, self.initial_settings.get('assistant_name', ''))
        self.mcp_use_external_var.set(self.initial_settings.get('mcp_use_external_python_server', False))
        self.mcp_script_path_entry.delete(0, tk.END)
        self.mcp_script_path_entry.insert(0, self.initial_settings.get('mcp_external_python_script_path', ''))
        self.toggle_mcp_script_path_entry()


class ChatUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Virtual Assistant")
        self.geometry("500x650")
        self.configure(bg='#1a1a1a')
        
        self.save_settings_callback = None # To be set by the Application class
        self.current_settings_for_modal = {} # Will be populated by Application
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

    def update_settings_for_modal(self, settings: dict):
        """Stores the current settings to be passed to the settings modal."""
        self.current_settings_for_modal = settings.copy()
        if self.settings_modal and self.settings_modal.winfo_exists(): # If modal already exists, update its field
            self.settings_modal.update_modal_fields(self.current_settings_for_modal)

    def open_settings_modal(self):
        """Opens the settings modal window."""
        if not self.settings_modal or not self.settings_modal.winfo_exists():
            self.settings_modal = SettingsModal(
                self, 
                initial_settings=self.current_settings_for_modal,
                save_callback=self.save_settings_callback
            )
        else:
            self.settings_modal.deiconify() # If minimized, restore it
        self.settings_modal.grab_set() # Ensure modal is focused
        self.wait_window(self.settings_modal) # Wait for the modal to close
