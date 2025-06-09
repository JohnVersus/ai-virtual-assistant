# src/ui/gui.py
import tkinter as tk
from tkinter import ttk, messagebox
import math
from ..config.settings import save_settings, load_settings

class ModernUI(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Virtual Assistant")
        self.geometry("400x500")
        self.configure(bg='#1a1a1a')
        self.resizable(False, False)

        self.settings = load_settings()
        
        # Animation variables
        self.animation_frame = 0
        self.animation_running = False
        self.animation_after_id = None
        self.current_state = "idle"
        
        self.setup_ui()

    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self, bg='#1a1a1a', padx=30, pady=30)
        main_frame.pack(expand=True, fill="both")

        # Title
        title_label = tk.Label(
            main_frame,
            text="AI Assistant",
            font=("Helvetica", 24, "bold"),
            fg='#ffffff',
            bg='#1a1a1a'
        )
        title_label.pack(pady=(0, 30))

        # Sound wave canvas
        self.canvas = tk.Canvas(
            main_frame,
            width=300,
            height=120,
            bg='#1a1a1a',
            highlightthickness=0
        )
        self.canvas.pack(pady=20)

        # Status text
        self.status_label = tk.Label(
            main_frame,
            text="Initializing...",
            font=("Helvetica", 18),
            fg='#ffffff',
            bg='#1a1a1a',
            wraplength=350,
            justify="center"
        )
        self.status_label.pack(pady=30)

        # Settings button
        settings_button = tk.Button(
            main_frame,
            text="⚙ Settings",
            font=("Helvetica", 12),
            fg='#ffffff',
            bg='#333333',
            activebackground='#555555',
            activeforeground='#ffffff',
            border=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.open_settings
        )
        settings_button.pack(pady=(50, 0))

        # Initial state
        self.draw_sound_wave("listening")

    def draw_sound_wave(self, state):
        """Draw animated sound wave based on state"""
        self.canvas.delete("all")
        
        center_x = 150
        center_y = 60
        
        if state == "listening":
            # Gentle wave for listening
            color = '#4a9eff'
            amplitude = 15
            frequency = 2
            speed = 0.5
        elif state == "thinking":
            # More active wave for thinking
            color = '#ffa500'
            amplitude = 25
            frequency = 3
            speed = 1.0
        elif state == "speaking":
            # Very active wave for speaking
            color = '#00ff88'
            amplitude = 35
            frequency = 4
            speed = 1.5
        elif state == "waiting":
            # Slow gentle wave for waiting
            color = '#ffaa00'
            amplitude = 10
            frequency = 1
            speed = 0.3
        else:
            # Default idle state
            color = '#666666'
            amplitude = 5
            frequency = 1
            speed = 0.2

        # Draw multiple wave lines
        for wave_num in range(3):
            points = []
            wave_offset = wave_num * 0.5
            wave_amplitude = amplitude * (1 - wave_num * 0.3)
            
            for x in range(0, 300, 2):
                # Create wave equation
                wave_x = x - 150
                time_factor = self.animation_frame * speed * 0.1
                y_offset = wave_amplitude * math.sin(
                    (wave_x * frequency * 0.02) + time_factor + wave_offset
                )
                
                points.extend([x, center_y + y_offset])
            
            # Draw the wave line
            if len(points) >= 4:
                self.canvas.create_line(
                    points,
                    fill=color,
                    width=2 - wave_num,
                    smooth=True,
                    tags=f'wave_{wave_num}'
                )

        # Draw center indicator dot
        dot_size = 3 + (amplitude * 0.1)
        self.canvas.create_oval(
            center_x - dot_size, center_y - dot_size,
            center_x + dot_size, center_y + dot_size,
            fill=color,
            outline='',
            tags='center_dot'
        )

    def animate(self):
        """Animation loop"""
        if self.animation_running:
            self.animation_frame += 1
            self.draw_sound_wave(self.current_state)
            self.animation_after_id = self.after(50, self.animate)

    def start_animation(self):
        """Start the animation loop"""
        if not self.animation_running:
            self.animation_running = True
            self.animate()

    def stop_animation(self):
        """Stop the animation loop"""
        self.animation_running = False
        if self.animation_after_id:
            self.after_cancel(self.animation_after_id)
            self.animation_after_id = None

    def set_status(self, text, state="idle"):
        """Update status with visual indicator"""
        self.status_label.config(text=text)
        self.current_state = state
        
        # Set text color based on state
        color_map = {
            "listening": '#4a9eff',
            "thinking": '#ffa500', 
            "speaking": '#00ff88',
            "waiting": '#ffaa00',
            "error": '#ff4444'
        }
        
        self.status_label.config(fg=color_map.get(state, '#ffffff'))
        
        # Start animation for active states
        if state in ["listening", "thinking", "speaking", "waiting"]:
            self.start_animation()
        else:
            self.stop_animation()
            self.draw_sound_wave(state)

    def open_settings(self):
        settings_window = tk.Toplevel(self)
        settings_window.title("Assistant Settings")
        settings_window.geometry("350x250")
        settings_window.configure(bg='#1a1a1a')
        settings_window.resizable(False, False)
        
        # Center the window
        settings_window.transient(self)
        settings_window.grab_set()

        # Main frame
        settings_frame = tk.Frame(settings_window, bg='#1a1a1a', padx=30, pady=30)
        settings_frame.pack(expand=True, fill="both")

        # Title
        title_label = tk.Label(
            settings_frame,
            text="Settings",
            font=("Helvetica", 18, "bold"),
            fg='#ffffff',
            bg='#1a1a1a'
        )
        title_label.pack(pady=(0, 30))

        # Assistant name section
        name_label = tk.Label(
            settings_frame,
            text="Wake Word:",
            font=("Helvetica", 12),
            fg='#ffffff',
            bg='#1a1a1a'
        )
        name_label.pack(pady=(0, 10), anchor='w')
        
        self.name_entry = tk.Entry(
            settings_frame,
            font=("Helvetica", 12),
            bg='#333333',
            fg='#ffffff',
            insertbackground='#ffffff',
            relief='flat',
            padx=15,
            pady=10,
            width=25
        )
        self.name_entry.insert(0, self.settings.get('assistant_name', 'gemini'))
        self.name_entry.pack(pady=(0, 30), fill='x')

        # Buttons frame
        buttons_frame = tk.Frame(settings_frame, bg='#1a1a1a')
        buttons_frame.pack(fill='x')

        # Save button
        save_button = tk.Button(
            buttons_frame,
            text="Save Settings",
            font=("Helvetica", 12, "bold"),
            fg='#ffffff',
            bg='#4a9eff',
            activebackground='#3a8eef',
            activeforeground='#ffffff',
            border=0,
            padx=25,
            pady=10,
            cursor="hand2",
            command=lambda: self.save_assistant_name(settings_window)
        )
        save_button.pack(side='left', padx=(0, 15))

        # Cancel button
        cancel_button = tk.Button(
            buttons_frame,
            text="Cancel",
            font=("Helvetica", 12),
            fg='#ffffff',
            bg='#666666',
            activebackground='#555555',
            activeforeground='#ffffff',
            border=0,
            padx=25,
            pady=10,
            cursor="hand2",
            command=settings_window.destroy
        )
        cancel_button.pack(side='left')

    def save_assistant_name(self, window):
        new_name = self.name_entry.get().strip()
        if new_name:
            self.settings['assistant_name'] = new_name
            save_settings(self.settings)
            
            # Show success message
            messagebox.showinfo(
                "Settings Saved", 
                "Assistant name updated!\nPlease restart the app for changes to take effect.",
                parent=window
            )
            window.destroy()
        else:
            # Show warning
            messagebox.showwarning(
                "Invalid Input", 
                "Wake word cannot be empty.",
                parent=window
            )