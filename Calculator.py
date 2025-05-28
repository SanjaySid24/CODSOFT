import tkinter as tk
from tkinter import ttk, messagebox
import ttkbootstrap as ttkb
from ttkbootstrap.constants import *
import math
import numpy as np
from datetime import datetime

class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Calculator")
        self.root.geometry("500x700")

        # Initialize style with a modern theme
        self.style = ttkb.Style(theme="flatly")
        self.is_dark_mode = False
        self.is_scientific_mode = False

        # Define custom colors for light and dark modes
        self.colors = {
            "light": {
                "bg": "#F5F5F5",  # Off-white background
                "number_btn": "#A3BFFA",  # Light blue for number buttons
                "number_text": "#000000",  # Black text for number buttons
                "operator_btn": "#4FD1C5",  # Teal for operator buttons
                "operator_text": "#FFFFFF",  # White text for operators
                "special_btn_warning": "#F6AD55",  # Orange for Clear, Backspace
                "special_btn_success": "#68D391",  # Green for Equals
                "special_text": "#FFFFFF",  # White text for special buttons
                "text": "#000000",  # Black text for labels
            },
            "dark": {
                "bg": "#2D3748",  # Dark gray background
                "number_btn": "#4A5568",  # Dark blue for number buttons
                "number_text": "#FFFFFF",  # White text for number buttons
                "operator_btn": "#38B2AC",  # Teal for operator buttons
                "operator_text": "#FFFFFF",  # White text for operators
                "special_btn_warning": "#DD6B20",  # Orange for Clear, Backspace
                "special_btn_success": "#48BB78",  # Green for Equals
                "special_text": "#FFFFFF",  # White text for special buttons
                "text": "#FFFFFF",  # White text for labels
            }
        }

        # Set initial background color
        self.current_mode = "light"
        self.root.configure(bg=self.colors[self.current_mode]["bg"])

        # History list to store past calculations
        self.history = []

        # Main frame
        self.main_frame = ttkb.Frame(self.root, padding=10, style="TFrame")
        self.main_frame.pack(fill=BOTH, expand=True)

        # Display frame
        self.display_frame = ttkb.Frame(self.main_frame)
        self.display_frame.pack(fill=X)

        # Entry display for calculations
        self.display_var = tk.StringVar()
        self.display_entry = ttkb.Entry(
            self.display_frame, textvariable=self.display_var, font=("Helvetica", 20), justify="right", state="readonly"
        )
        self.display_entry.pack(fill=X, pady=5)

        # Mode and Theme toggle buttons
        self.toggle_frame = ttkb.Frame(self.main_frame)
        self.toggle_frame.pack(fill=X, pady=5)

        self.mode_button = ttkb.Button(
            self.toggle_frame, text="Standard Mode", command=self.toggle_mode, bootstyle="outline-primary"
        )
        self.mode_button.pack(side=LEFT, padx=5)

        self.theme_button = ttkb.Button(
            self.toggle_frame, text="🌙 Dark Mode", command=self.toggle_theme, bootstyle="outline-primary"
        )
        self.theme_button.pack(side=RIGHT, padx=5)

        # History panel (scrollable)
        self.history_frame = ttkb.LabelFrame(self.main_frame, text="History", padding=5)
        self.history_frame.pack(fill=BOTH, pady=5)

        self.history_canvas = tk.Canvas(self.history_frame, height=100, highlightthickness=0)
        self.history_scrollbar = ttkb.Scrollbar(self.history_frame, orient=VERTICAL, command=self.history_canvas.yview)
        self.history_inner_frame = ttkb.Frame(self.history_canvas)

        self.history_inner_frame.bind(
            "<Configure>", lambda e: self.history_canvas.configure(scrollregion=self.history_canvas.bbox("all"))
        )

        self.history_canvas.configure(yscrollcommand=self.history_scrollbar.set)
        self.history_canvas.create_window((0, 0), window=self.history_inner_frame, anchor="nw")

        self.history_scrollbar.pack(side=RIGHT, fill=Y)
        self.history_canvas.pack(side=LEFT, fill=BOTH, expand=True)

        # Clear History Button
        self.clear_history_button = ttkb.Button(
            self.main_frame, text="Clear History", command=self.clear_history, style="Warning.TButton", width=15
        )
        self.clear_history_button.pack(pady=5)

        # Button frame
        self.button_frame = ttkb.Frame(self.main_frame)
        self.button_frame.pack(fill=BOTH, expand=True)

        # Initialize buttons
        self.buttons = {}
        self.update_colors()  # Set initial colors
        self.create_buttons()

        # Bind keyboard input
        self.root.bind("<Key>", self.handle_keypress)
        self.root.bind("<Return>", lambda event: self.calculate())
        self.root.bind("<BackSpace>", lambda event: self.backspace())

    def toggle_theme(self):
        """Toggle between light and dark mode."""
        self.is_dark_mode = not self.is_dark_mode
        self.current_mode = "dark" if self.is_dark_mode else "light"
        self.style.theme_use("darkly" if self.is_dark_mode else "flatly")
        self.theme_button.configure(text="☀️ Light Mode" if self.is_dark_mode else "🌙 Dark Mode")
        self.update_colors()
        self.create_buttons()  # Recreate buttons to apply new colors

    def update_colors(self):
        """Update the colors of the UI elements based on the current mode."""
        mode = self.current_mode
        self.root.configure(bg=self.colors[mode]["bg"])
        self.history_canvas.configure(bg=self.colors[mode]["bg"])
        self.history_frame.configure(bootstyle=f"secondary")  # Adjust frame style
        self.display_entry.configure(bootstyle=f"secondary")  # Adjust entry style
        for widget in self.history_inner_frame.winfo_children():
            widget.configure(foreground=self.colors[mode]["text"])

    def toggle_mode(self):
        """Toggle between Standard and Scientific mode."""
        self.is_scientific_mode = not self.is_scientific_mode
        self.mode_button.configure(text="Scientific Mode" if not self.is_scientific_mode else "Standard Mode")
        self.create_buttons()

    def create_buttons(self):
        """Create calculator buttons based on the current mode with custom colors."""
        # Clear existing buttons
        for widget in self.button_frame.winfo_children():
            widget.destroy()
        self.buttons.clear()

        mode = self.current_mode

        # Define button styles
        number_style = ttkb.Style()
        number_style.configure(
            "Number.TButton",
            background=self.colors[mode]["number_btn"],
            foreground=self.colors[mode]["number_text"],
            font=("Helvetica", 12)
        )

        operator_style = ttkb.Style()
        operator_style.configure(
            "Operator.TButton",
            background=self.colors[mode]["operator_btn"],
            foreground=self.colors[mode]["operator_text"],
            font=("Helvetica", 12)
        )

        warning_style = ttkb.Style()
        warning_style.configure(
            "Warning.TButton",
            background=self.colors[mode]["special_btn_warning"],
            foreground=self.colors[mode]["special_text"],
            font=("Helvetica", 12)
        )

        success_style = ttkb.Style()
        success_style.configure(
            "Success.TButton",
            background=self.colors[mode]["special_btn_success"],
            foreground=self.colors[mode]["special_text"],
            font=("Helvetica", 12)
        )

        # Button layout for standard mode
        button_layout = [
            ("C", 0, 0, self.clear, "Warning.TButton"),
            ("(", 0, 1, lambda: self.append_to_display("("), "Operator.TButton"),
            (")", 0, 2, lambda: self.append_to_display(")"), "Operator.TButton"),
            ("/", 0, 3, lambda: self.append_to_display("/"), "Operator.TButton"),
            ("7", 1, 0, lambda: self.append_to_display("7"), "Number.TButton"),
            ("8", 1, 1, lambda: self.append_to_display("8"), "Number.TButton"),
            ("9", 1, 2, lambda: self.append_to_display("9"), "Number.TButton"),
            ("*", 1, 3, lambda: self.append_to_display("*"), "Operator.TButton"),
            ("4", 2, 0, lambda: self.append_to_display("4"), "Number.TButton"),
            ("5", 2, 1, lambda: self.append_to_display("5"), "Number.TButton"),
            ("6", 2, 2, lambda: self.append_to_display("6"), "Number.TButton"),
            ("-", 2, 3, lambda: self.append_to_display("-"), "Operator.TButton"),
            ("1", 3, 0, lambda: self.append_to_display("1"), "Number.TButton"),
            ("2", 3, 1, lambda: self.append_to_display("2"), "Number.TButton"),
            ("3", 3, 2, lambda: self.append_to_display("3"), "Number.TButton"),
            ("+", 3, 3, lambda: self.append_to_display("+"), "Operator.TButton"),
            ("0", 4, 0, lambda: self.append_to_display("0"), "Number.TButton"),
            (".", 4, 1, lambda: self.append_to_display("."), "Number.TButton"),
            ("⌫", 4, 2, self.backspace, "Warning.TButton"),
            ("=", 4, 3, self.calculate, "Success.TButton"),
        ]

        # Add scientific buttons if in scientific mode
        if self.is_scientific_mode:
            scientific_buttons = [
                ("√", 0, 4, lambda: self.append_to_display("sqrt("), "Operator.TButton"),
                ("^", 1, 4, lambda: self.append_to_display("**"), "Operator.TButton"),
                ("sin", 2, 4, lambda: self.append_to_display("sin("), "Operator.TButton"),
                ("cos", 3, 4, lambda: self.append_to_display("cos("), "Operator.TButton"),
                ("tan", 4, 4, lambda: self.append_to_display("tan("), "Operator.TButton"),
                ("log", 5, 4, lambda: self.append_to_display("log10("), "Operator.TButton"),
            ]
            button_layout.extend(scientific_buttons)

        # Create buttons
        for (text, row, col, command, style) in button_layout:
            btn = ttkb.Button(self.button_frame, text=text, command=command, style=style, width=5)
            btn.grid(row=row, column=col, padx=2, pady=2, sticky="nsew")
            self.buttons[text] = btn

        # Configure grid weights for responsiveness
        for i in range(5 if not self.is_scientific_mode else 6):
            self.button_frame.grid_rowconfigure(i, weight=1)
        for i in range(4 if not self.is_scientific_mode else 5):
            self.button_frame.grid_columnconfigure(i, weight=1)

    def clear_history(self):
        """Clear the history list and update the history panel."""
        self.history = []  # Clear the history list
        self.update_history()  # Refresh the history panel

    def append_to_display(self, char):
        """Append a character to the display."""
        current = self.display_var.get()
        self.display_var.set(current + char)

    def clear(self):
        """Clear the display."""
        self.display_var.set("")

    def backspace(self):
        """Remove the last character from the display."""
        current = self.display_var.get()
        self.display_var.set(current[:-1])

    def calculate(self):
        """Evaluate the expression in the display and handle errors."""
        expression = self.display_var.get()
        if not expression:
            return

        try:
            # Replace scientific functions with numpy equivalents
            expression = expression.replace("sin(", "np.sin(np.radians(")
            expression = expression.replace("cos(", "np.cos(np.radians(")
            expression = expression.replace("tan(", "np.tan(np.radians(")
            expression = expression.replace("sqrt(", "np.sqrt(")
            expression = expression.replace("log10(", "np.log10(")

            # Evaluate the expression
            result = eval(expression, {"np": np, "math": math})
            self.display_var.set(str(result))

            # Add to history
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.history.append(f"{timestamp}: {expression} = {result}")
            self.update_history()

        except ZeroDivisionError:
            messagebox.showerror("Error", "Division by zero is not allowed!")
            self.clear()
        except Exception as e:
            messagebox.showerror("Error", f"Invalid expression: {str(e)}")
            self.clear()

    def update_history(self):
        """Update the history panel with past calculations."""
        for widget in self.history_inner_frame.winfo_children():
            widget.destroy()

        # Show last 10 entries
        for entry in self.history[-10:]:
            label = ttkb.Label(
                self.history_inner_frame, 
                text=entry, 
                font=("Helvetica", 10), 
                foreground=self.colors[self.current_mode]["text"]
            )
            label.pack(anchor="w", pady=2)

    def handle_keypress(self, event):
        """Handle keyboard input for numbers, operators, and other keys."""
        char = event.char
        if char in "0123456789.+-*/()":
            self.append_to_display(char)
        elif char == "^":
            self.append_to_display("**")
        elif char.lower() == "s" and self.is_scientific_mode:
            self.append_to_display("sin(")
        elif char.lower() == "c" and self.is_scientific_mode:
            self.append_to_display("cos(")
        elif char.lower() == "t" and self.is_scientific_mode:
            self.append_to_display("tan(")
        elif char.lower() == "l" and self.is_scientific_mode:
            self.append_to_display("log10(")
        elif char.lower() == "r" and self.is_scientific_mode:
            self.append_to_display("sqrt(")

if __name__ == "__main__":
    root = ttkb.Window()
    app = CalculatorApp(root)
    root.mainloop()