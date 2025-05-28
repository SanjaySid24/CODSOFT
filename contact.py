import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import json
import re
import os
from datetime import datetime
import csv
from PIL import Image, ImageTk
import base64
from io import BytesIO

# Try importing fuzzywuzzy, fallback to standard search if not available
try:
    from fuzzywuzzy import process as fuzzy
    FUZZY_AVAILABLE = True
except ImportError:
    FUZZY_AVAILABLE = False
    messagebox.showwarning("Warning", "fuzzywuzzy not installed. Using standard search instead.")

class ContactBook:
    def __init__(self, root):
        self.root = root
        self.root.title("Contact Manager")
        self.root.geometry("1000x700")
        self.contacts = []
        self.file_path = "contacts.json"
        self.activity_log = []
        self.groups = ["Work", "Family", "Friends"]
        self.favorites = set()
        self.recent_contacts = []

        # Load contacts
        self.load_contacts()

        # Style configuration
        self.style = ttk.Style()
        self.style.theme_use("flatly")  # Professional theme
        self.style.configure("TButton", font=("Segoe UI", 10), padding=8, background="#007bff", foreground="white")
        self.style.configure("TLabel", font=("Segoe UI", 11))
        self.style.configure("Treeview", font=("Segoe UI", 10))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))
        self.root.configure(background="#f8f9fa")  # Light gray background

        # Main container
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        self.header_frame = ttk.Frame(self.main_frame)
        self.header_frame.pack(fill="x", pady=(0, 10))
        ttk.Label(self.header_frame, text="Contact Manager", font=("Segoe UI", 16, "bold")).pack(side="left", padx=10)
        ttk.Button(self.header_frame, text="Toggle Theme", command=self.toggle_theme).pack(side="right", padx=5)

        # Create UI components
        self.create_menu()
        self.create_dashboard()
        self.create_contact_list()
        self.create_search_bar()
        self.create_buttons()

        # Bind shortcuts
        self.root.bind("<Control-n>", lambda event: self.show_add_contact_form())
        self.root.bind("<Control-s>", lambda event: self.search_contacts())
        self.root.bind("<Control-b>", lambda event: self.backup_contacts())

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        current_theme = self.style.theme_use()
        new_theme = "darkly" if current_theme == "flatly" else "flatly"
        self.style.theme_use(new_theme)
        self.root.configure(background="#212529" if new_theme == "darkly" else "#f8f9fa")
        self.style.configure("TButton", background="#007bff" if new_theme == "flatly" else "#17a2b8")

    def create_menu(self):
        """Create menu bar."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export to CSV", command=self.export_csv)
        file_menu.add_command(label="Export to VCF", command=self.export_vcf)
        file_menu.add_command(label="Import from CSV", command=self.import_csv)
        file_menu.add_command(label="Backup Contacts (Ctrl+B)", command=self.backup_contacts)
        file_menu.add_command(label="Restore Contacts", command=self.restore_contacts)
        file_menu.add_command(label="Exit", command=self.root.quit)

        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Show Activity Log", command=self.show_activity_log)
        view_menu.add_command(label="Show Statistics", command=self.show_statistics)

    def create_dashboard(self):
        """Create dashboard for stats and recent contacts."""
        dashboard_frame = ttk.Frame(self.main_frame)
        dashboard_frame.pack(fill="x", pady=10)

        ttk.Label(dashboard_frame, text=f"Total Contacts: {len(self.contacts)}").pack(side="left", padx=10)
        ttk.Label(dashboard_frame, text=f"Favorites: {len(self.favorites)}").pack(side="left", padx=10)
        ttk.Button(dashboard_frame, text="Recent Contacts", command=self.show_recent_contacts).pack(side="right", padx=5)

    def create_contact_list(self):
        """Create contact list table."""
        self.tree_frame = ttk.Frame(self.main_frame)
        self.tree_frame.pack(fill="both", expand=True)

        self.tree = ttk.Treeview(self.tree_frame, columns=("Name", "Phone", "Email", "Category", "Tags"), show="headings")
        self.tree.heading("Name", text="Name", command=lambda: self.sort_contacts("Name"))
        self.tree.heading("Phone", text="Phone", command=lambda: self.sort_contacts("Phone"))
        self.tree.heading("Email", text="Email", command=lambda: self.sort_contacts("Email"))
        self.tree.heading("Category", text="Category", command=lambda: self.sort_contacts("Category"))
        self.tree.heading("Tags", text="Tags", command=lambda: self.sort_contacts("Tags"))
        self.tree.column("Name", width=200)
        self.tree.column("Phone", width=150)
        self.tree.column("Email", width=200)
        self.tree.column("Category", width=100)
        self.tree.column("Tags", width=100)
        self.tree.pack(fill="both", expand=True)

        scrollbar = ttk.Scrollbar(self.tree_frame, orient="vertical", command=self.tree.yview)
        scrollbar.pack(side="right", fill="y")
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.bind("<Double-1>", self.edit_contact)
        self.update_contact_list()

    def create_search_bar(self):
        """Create search bar and filters."""
        search_frame = ttk.Frame(self.main_frame)
        search_frame.pack(fill="x", pady=5)

        ttk.Label(search_frame, text="Search:").pack(side="left")
        self.search_var = tk.StringVar()
        self.search_entry = ttk.Entry(search_frame, textvariable=self.search_var)
        self.search_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.search_entry.bind("<Return>", lambda event: self.search_contacts())

        ttk.Label(search_frame, text="Category:").pack(side="left", padx=5)
        self.category_var = tk.StringVar()
        self.category_combo = ttk.Combobox(search_frame, textvariable=self.category_var, values=["All"] + self.groups)
        self.category_combo.pack(side="left", padx=5)
        self.category_combo.current(0)
        self.category_combo.bind("<<ComboboxSelected>>", lambda event: self.search_contacts())

    def create_buttons(self):
        """Create action buttons."""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill="x", pady=10)

        buttons = [
            ("Add Contact (Ctrl+N)", self.show_add_contact_form),
            ("Delete Selected", self.delete_contact),
            ("Show Details", self.show_contact_details),
            ("Mark Favorite", self.toggle_favorite),
            ("Send Email", self.send_email),
            ("Manage Groups", self.manage_groups)
        ]
        for text, command in buttons:
            ttk.Button(button_frame, text=text, command=command, style="TButton").pack(side="left", padx=5)

    def load_contacts(self):
        """Load contacts from JSON file."""
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, "r") as file:
                    self.contacts = json.load(file)
            except json.JSONDecodeError:
                self.contacts = []
                self.log_activity("Failed to load contacts: Invalid JSON format")

    def save_contacts(self):
        """Save contacts to JSON file."""
        try:
            with open(self.file_path, "w") as file:
                json.dump(self.contacts, file, indent=4)
            self.log_activity("Saved contacts to file")
        except Exception as e:
            self.log_activity(f"Failed to save contacts: {str(e)}")
            messagebox.showerror("Error", "Failed to save contacts")

    def validate_email(self, email):
        """Validate email format."""
        if not email:
            return True
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    def validate_phone(self, phone):
        """Validate phone number format."""
        if not phone:
            return True
        pattern = r'^\+?1?\d{10,15}$'
        return re.match(pattern, phone) is not None

    def show_add_contact_form(self):
        """Show form to add a new contact."""
        print("Opening Add Contact form")  # Debug output
        form_window = ttk.Toplevel(self.root)
        form_window.title("Add Contact")
        form_window.geometry("500x600")

        fields = ["Name", "Phone", "Email", "Address", "Category", "Tags", "Notes"]
        entries = {}
        self.image_data = None

        # Create form fields
        for i, field in enumerate(fields):
            label = ttk.Label(form_window, text=f"{field}:")
            label.grid(row=i, column=0, padx=10, pady=5, sticky="e")
            if field == "Category":
                entry = ttk.Combobox(form_window, values=self.groups)
                entry.current(0)
            else:
                entry = ttk.Entry(form_window)
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="we")
            entries[field] = entry

        # Upload image button
        def upload_image():
            file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
            if file_path:
                try:
                    with open(file_path, "rb") as image_file:
                        self.image_data = base64.b64encode(image_file.read()).decode("utf-8")
                    messagebox.showinfo("Success", "Image uploaded successfully")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to upload image: {str(e)}")

        ttk.Button(form_window, text="Upload Profile Picture", command=upload_image).grid(row=len(fields), column=0, columnspan=2, pady=10)

        # Submit button
        def submit():
            contact = {field.lower(): entries[field].get() for field in fields}
            contact["image"] = self.image_data

            # Validate inputs
            if not contact["name"]:
                messagebox.showerror("Error", "Name is required")
                return
            if contact["phone"] and not self.validate_phone(contact["phone"]):
                messagebox.showerror("Error", "Invalid phone number")
                return
            if contact["email"] and not self.validate_email(contact["email"]):
                messagebox.showerror("Error", "Invalid email address")
                return

            # Check for duplicate
            if any(c["name"].lower() == contact["name"].lower() and c["phone"] == contact["phone"] for c in self.contacts):
                messagebox.showerror("Error", "Contact already exists")
                return

            self.contacts.append(contact)
            self.recent_contacts.append(contact["name"])
            if len(self.recent_contacts) > 5:
                self.recent_contacts.pop(0)
            self.save_contacts()
            self.update_contact_list()
            self.log_activity(f"Added contact: {contact['name']}")
            form_window.destroy()
            print("Contact added successfully")  # Debug output

        ttk.Button(form_window, text="Submit", command=submit, style="TButton").grid(row=len(fields)+1, column=0, columnspan=2, pady=10)

        # Ensure form window is visible
        form_window.update()
        form_window.lift()
        print("Add Contact form created")  # Debug output

    def update_contact_list(self):
        """Update the contact list display."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        for contact in self.contacts:
            self.tree.insert("", "end", values=(
                contact.get("name", ""),
                contact.get("phone", ""),
                contact.get("email", ""),
                contact.get("category", ""),
                contact.get("tags", "")
            ))

    def search_contacts(self):
        """Advanced search with fuzzy matching if available."""
        query = self.search_var.get().lower()
        category = self.category_var.get()
        filtered_contacts = self.contacts

        if query:
            if FUZZY_AVAILABLE:
                names = [c.get("name", "") for c in self.contacts]
                matches = fuzzy.extractBests(query, names, score_cutoff=70, limit=10)
                matched_names = [match[0] for match in matches]
                filtered_contacts = [
                    c for c in filtered_contacts if (
                        c.get("name", "").lower() in matched_names or
                        query in c.get("phone", "").lower() or
                        query in c.get("email", "").lower() or
                        query in c.get("address", "").lower() or
                        query in c.get("notes", "").lower() or
                        query in c.get("tags", "").lower()
                    )
                ]
            else:
                filtered_contacts = [
                    c for c in filtered_contacts if (
                        query in c.get("name", "").lower() or
                        query in c.get("phone", "").lower() or
                        query in c.get("email", "").lower() or
                        query in c.get("address", "").lower() or
                        query in c.get("notes", "").lower() or
                        query in c.get("tags", "").lower()
                    )
                ]

        if category != "All":
            filtered_contacts = [c for c in filtered_contacts if c.get("category", "") == category]

        for item in self.tree.get_children():
            self.tree.delete(item)
        for contact in filtered_contacts:
            self.tree.insert("", "end", values=(
                contact.get("name", ""),
                contact.get("phone", ""),
                contact.get("email", ""),
                contact.get("category", ""),
                contact.get("tags", "")
            ))

    def edit_contact(self, event):
        """Edit selected contact."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a contact to edit")
            return

        index = self.tree.index(selected_item[0])
        contact = self.contacts[index]

        form_window = ttk.Toplevel(self.root)
        form_window.title("Edit Contact")
        form_window.geometry("500x600")

        fields = ["Name", "Phone", "Email", "Address", "Category", "Tags", "Notes"]
        entries = {}
        self.image_data = contact.get("image")

        for i, field in enumerate(fields):
            ttk.Label(form_window, text=f"{field}:").grid(row=i, column=0, padx=10, pady=5, sticky="e")
            if field == "Category":
                entry = ttk.Combobox(form_window, values=self.groups)
                entry.set(contact.get(field.lower(), ""))
            else:
                entry = ttk.Entry(form_window)
                entry.insert(0, contact.get(field.lower(), ""))
            entry.grid(row=i, column=1, padx=10, pady=5, sticky="we")
            entries[field] = entry

        def upload_image():
            file_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg")])
            if file_path:
                try:
                    with open(file_path, "rb") as image_file:
                        self.image_data = base64.b64encode(image_file.read()).decode("utf-8")
                    messagebox.showinfo("Success", "Image uploaded successfully")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to upload image: {str(e)}")

        ttk.Button(form_window, text="Upload Profile Picture", command=upload_image).grid(row=len(fields), column=0, columnspan=2, pady=10)

        def submit():
            updated_contact = {field.lower(): entries[field].get() for field in fields}
            updated_contact["image"] = self.image_data

            if not updated_contact["name"]:
                messagebox.showerror("Error", "Name is required")
                return
            if updated_contact["phone"] and not self.validate_phone(updated_contact["phone"]):
                messagebox.showerror("Error", "Invalid phone number")
                return
            if updated_contact["email"] and not self.validate_email(updated_contact["email"]):
                messagebox.showerror("Error", "Invalid email address")
                return

            self.contacts[index] = updated_contact
            if updated_contact["name"] not in self.recent_contacts:
                self.recent_contacts.append(updated_contact["name"])
                if len(self.recent_contacts) > 5:
                    self.recent_contacts.pop(0)
            self.save_contacts()
            self.update_contact_list()
            self.log_activity(f"Updated contact: {updated_contact['name']}")
            form_window.destroy()

        ttk.Button(form_window, text="Submit", command=submit, style="TButton").grid(row=len(fields)+1, column=0, columnspan=2, pady=10)

    def delete_contact(self):
        """Delete selected contact."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a contact to delete")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete this contact?"):
            index = self.tree.index(selected_item[0])
            contact_name = self.contacts[index]["name"]
            if contact_name in self.favorites:
                self.favorites.remove(contact_name)
            if contact_name in self.recent_contacts:
                self.recent_contacts.remove(contact_name)
            del self.contacts[index]
            self.save_contacts()
            self.update_contact_list()
            self.log_activity(f"Deleted contact: {contact_name}")

    def show_contact_details(self):
        """Show detailed information of selected contact."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a contact to view details")
            return

        index = self.tree.index(selected_item[0])
        contact = self.contacts[index]

        details_window = ttk.Toplevel(self.root)
        details_window.title("Contact Details")
        details_window.geometry("400x500")

        if contact.get("image"):
            try:
                img_data = base64.b64decode(contact["image"])
                img = Image.open(BytesIO(img_data))
                img = img.resize((100, 100), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                ttk.Label(details_window, image=photo).pack(pady=10)
                details_window.photo = photo  # Keep reference
            except Exception as e:
                messagebox.showwarning("Warning", f"Failed to load image: {str(e)}")

        for key, value in contact.items():
            if key != "image":
                ttk.Label(details_window, text=f"{key.capitalize()}: {value}").pack(pady=5)

    def toggle_favorite(self):
        """Mark or unmark contact as favorite."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a contact")
            return
        index = self.tree.index(selected_item[0])
        contact_name = self.contacts[index]["name"]
        if contact_name in self.favorites:
            self.favorites.remove(contact_name)
            self.log_activity(f"Removed {contact_name} from favorites")
        else:
            self.favorites.add(contact_name)
            self.log_activity(f"Added {contact_name} to favorites")
        self.update_contact_list()

    def send_email(self):
        """Simulate sending an email to selected contact."""
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("Warning", "Please select a contact")
            return
        index = self.tree.index(selected_item[0])
        contact = self.contacts[index]
        if not contact.get("email"):
            messagebox.showerror("Error", "No email address for this contact")
            return
        messagebox.showinfo("Success", f"Simulated email sent to {contact['email']}")
        self.log_activity(f"Sent email to {contact['name']}")

    def manage_groups(self):
        """Manage contact groups."""
        group_window = ttk.Toplevel(self.root)
        group_window.title("Manage Groups")
        group_window.geometry("300x400")

        ttk.Label(group_window, text="Current Groups:").pack(pady=5)
        for group in self.groups:
            ttk.Label(group_window, text=group).pack()

        ttk.Label(group_window, text="Add New Group:").pack(pady=10)
        group_var = tk.StringVar()
        group_entry = ttk.Entry(group_window, textvariable=group_var)
        group_entry.pack(padx=10, fill="x")

        def add_group():
            group_name = group_var.get().strip()
            if group_name and group_name not in self.groups:
                self.groups.append(group_name)
                self.log_activity(f"Added group: {group_name}")
                messagebox.showinfo("Success", f"Group {group_name} added")
                group_window.destroy()
                self.category_combo["values"] = ["All"] + self.groups

        ttk.Button(group_window, text="Add Group", command=add_group, style="TButton").pack(pady=10)

    def sort_contacts(self, column):
        """Sort contacts by specified column."""
        self.contacts.sort(key=lambda x: x.get(column.lower(), "").lower())
        self.update_contact_list()

    def export_csv(self):
        """Export contacts to CSV file."""
        try:
            with open("contacts_export.csv", "w", newline="") as file:
                writer = csv.DictWriter(file, fieldnames=["name", "phone", "email", "address", "category", "tags", "notes"])
                writer.writeheader()
                writer.writerows(self.contacts)
            self.log_activity("Exported contacts to CSV")
            messagebox.showinfo("Success", "Contacts exported to contacts_export.csv")
        except Exception as e:
            self.log_activity(f"Failed to export contacts: {str(e)}")
            messagebox.showerror("Error", "Failed to export contacts")

    def export_vcf(self):
        """Export contacts to vCard (.vcf) file."""
        try:
            with open("contacts_export.vcf", "w") as file:
                for contact in self.contacts:
                    vcard = f"BEGIN:VCARD\nVERSION:3.0\nFN:{contact.get('name', '')}\n"
                    if contact.get("phone"):
                        vcard += f"TEL:{contact['phone']}\n"
                    if contact.get("email"):
                        vcard += f"EMAIL:{contact['email']}\n"
                    if contact.get("address"):
                        vcard += f"ADR:{contact['address']}\n"
                    vcard += "END:VCARD\n"
                    file.write(vcard)
            self.log_activity("Exported contacts to VCF")
            messagebox.showinfo("Success", "Contacts exported to contacts_export.vcf")
        except Exception as e:
            self.log_activity(f"Failed to export VCF: {str(e)}")
            messagebox.showerror("Error", "Failed to export contacts to VCF")

    def import_csv(self):
        """Import contacts from CSV file."""
        try:
            with open("contacts_import.csv", "r") as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if any(c["name"].lower() == row["name"].lower() and c["phone"] == row["phone"] for c in self.contacts):
                        continue
                    self.contacts.append(row)
            self.save_contacts()
            self.update_contact_list()
            self.log_activity("Imported contacts from CSV")
            messagebox.showinfo("Success", "Contacts imported from contacts_import.csv")
        except FileNotFoundError:
            self.log_activity("Failed to import: contacts_import.csv not found")
            messagebox.showerror("Error", "contacts_import.csv not found")
        except Exception as e:
            self.log_activity(f"Failed to import contacts: {str(e)}")
            messagebox.showerror("Error", "Failed to import contacts")

    def backup_contacts(self):
        """Backup contacts to a timestamped JSON file."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = f"contacts_backup_{timestamp}.json"
        try:
            with open(backup_path, "w") as file:
                json.dump(self.contacts, file, indent=4)
            self.log_activity(f"Created backup: {backup_path}")
            messagebox.showinfo("Success", f"Backup created: {backup_path}")
        except Exception as e:
            self.log_activity(f"Failed to create backup: {str(e)}")
            messagebox.showerror("Error", "Failed to create backup")

    def restore_contacts(self):
        """Restore contacts from a backup file."""
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if file_path:
            try:
                with open(file_path, "r") as file:
                    self.contacts = json.load(file)
                self.save_contacts()
                self.update_contact_list()
                self.log_activity(f"Restored contacts from {file_path}")
                messagebox.showinfo("Success", f"Contacts restored from {file_path}")
            except Exception as e:
                self.log_activity(f"Failed to restore contacts: {str(e)}")
                messagebox.showerror("Error", "Failed to restore contacts")

    def show_recent_contacts(self):
        """Show recently added/updated contacts."""
        recent_window = ttk.Toplevel(self.root)
        recent_window.title("Recent Contacts")
        recent_window.geometry("400x300")

        for name in self.recent_contacts:
            ttk.Label(recent_window, text=name).pack(pady=5)

    def show_statistics(self):
        """Show contact statistics."""
        stats_window = ttk.Toplevel(self.root)
        stats_window.title("Contact Statistics")
        stats_window.geometry("400x300")

        category_counts = {}
        for contact in self.contacts:
            category = contact.get("category", "Uncategorized")
            category_counts[category] = category_counts.get(category, 0) + 1

        ttk.Label(stats_window, text=f"Total Contacts: {len(self.contacts)}").pack(pady=5)
        ttk.Label(stats_window, text=f"Favorites: {len(self.favorites)}").pack(pady=5)
        for category, count in category_counts.items():
            ttk.Label(stats_window, text=f"{category}: {count}").pack(pady=5)

    def log_activity(self, action):
        """Log activity with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.activity_log.append(f"{timestamp}: {action}")
        if len(self.activity_log) > 50:
            self.activity_log.pop(0)

    def show_activity_log(self):
        """Show activity log."""
        log_window = ttk.Toplevel(self.root)
        log_window.title("Activity Log")
        log_window.geometry("400x400")

        log_text = tk.Text(log_window, height=20, width=50, font=("Segoe UI", 10))
        log_text.pack(pady=10)
        for entry in self.activity_log:
            log_text.insert(tk.END, entry + "\n")
        log_text.config(state="disabled")

if __name__ == "__main__":
    root = ttk.Window(themename="flatly")
    app = ContactBook(root)
    root.mainloop()