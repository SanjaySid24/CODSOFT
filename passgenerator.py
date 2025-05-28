import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import random
import string
import pyperclip

def generate_password():
    length = password_length.get()
    use_upper = var_upper.get()
    use_lower = var_lower.get()
    use_digits = var_digits.get()
    use_symbols = var_symbols.get()

    if not (use_upper or use_lower or use_digits or use_symbols):
        messagebox.showwarning("Warning", "Please select at least one character type.")
        return

    pool = ''
    if use_upper:
        pool += string.ascii_uppercase
    if use_lower:
        pool += string.ascii_lowercase
    if use_digits:
        pool += string.digits
    if use_symbols:
        pool += "!@#$%^&*()-_=+[]{}|;:,.<>?/"

    # Ensure at least one character from each selected type
    password = []
    if use_upper:
        password.append(random.choice(string.ascii_uppercase))
    if use_lower:
        password.append(random.choice(string.ascii_lowercase))
    if use_digits:
        password.append(random.choice(string.digits))
    if use_symbols:
        password.append(random.choice("!@#$%^&*()-_=+[]{}|;:,.<>?/"))

    while len(password) < length:
        password.append(random.choice(pool))

    random.shuffle(password)
    final_password = ''.join(password)
    password_entry.delete(0, tk.END)
    password_entry.insert(0, final_password)

def copy_to_clipboard():
    pwd = password_entry.get()
    if pwd:
        pyperclip.copy(pwd)
        messagebox.showinfo("Copied", "Password copied to clipboard!")

# Create main window
app = tk.Tk()
app.title("🔐 Password Generator")
app.geometry("400x400")
app.configure(bg="#e8f5e9")

# Style
style = ttk.Style()
style.configure("TCheckbutton", background="#e8f5e9", font=("Segoe UI", 10))
style.configure("TButton", font=("Segoe UI", 10))

# Title
title = tk.Label(app, text="Password Generator", font=("Segoe UI", 18, "bold"), bg="#e8f5e9", fg="#2e7d32")
title.pack(pady=10)

# Password Length
frame_length = tk.Frame(app, bg="#e8f5e9")
frame_length.pack(pady=10)
tk.Label(frame_length, text="Password Length:", font=("Segoe UI", 10), bg="#e8f5e9").pack(side=tk.LEFT)
password_length = tk.IntVar(value=12)
tk.Scale(frame_length, from_=8, to=128, orient="horizontal", variable=password_length, bg="#e8f5e9").pack(side=tk.LEFT)

# Options
frame_options = tk.Frame(app, bg="#e8f5e9")
frame_options.pack(pady=10)

var_upper = tk.BooleanVar(value=True)
var_lower = tk.BooleanVar(value=True)
var_digits = tk.BooleanVar(value=True)
var_symbols = tk.BooleanVar(value=False)

ttk.Checkbutton(frame_options, text="Uppercase (A-Z)", variable=var_upper).grid(row=0, column=0, sticky="w", padx=5)
ttk.Checkbutton(frame_options, text="Lowercase (a-z)", variable=var_lower).grid(row=1, column=0, sticky="w", padx=5)
ttk.Checkbutton(frame_options, text="Numbers (0-9)", variable=var_digits).grid(row=0, column=1, sticky="w", padx=5)
ttk.Checkbutton(frame_options, text="Symbols (!@#$...)", variable=var_symbols).grid(row=1, column=1, sticky="w", padx=5)

# Generate Button
ttk.Button(app, text="Generate Password", command=generate_password).pack(pady=15)

# Password Output
password_entry = tk.Entry(app, font=("Segoe UI", 12), width=30, justify="center", bd=2, relief="solid")
password_entry.pack(pady=5)

# Copy Button
ttk.Button(app, text="Copy to Clipboard", command=copy_to_clipboard).pack(pady=10)

# Start app
app.mainloop()
