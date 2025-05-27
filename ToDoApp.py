import sys
import sqlite3
from datetime import datetime, date
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLineEdit, QComboBox, QDateEdit, QListWidget, QListWidgetItem,
                             QLabel, QCheckBox, QFrame, QMessageBox, QDialog)
from PyQt5.QtCore import Qt, QDate, QPropertyAnimation, QRect
from PyQt5.QtGui import QIcon, QFont

# Database handling
class Database:
    def __init__(self, db_name="todo.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.upgrade_schema()

    def create_tables(self):
        """Initialize database tables."""
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT,
                due_date TEXT,
                completed INTEGER DEFAULT 0,
                created_at TEXT
            )
        ''')
        self.conn.commit()

    def upgrade_schema(self):
        """Add new columns if they don't exist."""
        # Check if columns exist
        self.cursor.execute("PRAGMA table_info(tasks)")
        columns = [info[1] for info in self.cursor.fetchall()]
        
        # Add is_daily column if missing
        if 'is_daily' not in columns:
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN is_daily INTEGER DEFAULT 0")
            self.conn.commit()
        
        # Add daily_completed_date column if missing
        if 'daily_completed_date' not in columns:
            self.cursor.execute("ALTER TABLE tasks ADD COLUMN daily_completed_date TEXT")
            self.conn.commit()

    def add_task(self, title, category, due_date, is_daily):
        """Add a new task."""
        created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.cursor.execute('''
            INSERT INTO tasks (title, category, due_date, created_at, is_daily)
            VALUES (?, ?, ?, ?, ?)
        ''', (title, category, due_date, created_at, is_daily))
        self.conn.commit()

    def get_tasks(self, completed=0, is_daily=None):
        """Retrieve tasks based on completion status or daily status."""
        if is_daily is None:
            self.cursor.execute("SELECT * FROM tasks WHERE completed = ?", (completed,))
        else:
            self.cursor.execute("SELECT * FROM tasks WHERE completed = ? AND is_daily = ?", (completed, is_daily))
        return self.cursor.fetchall()

    def update_task(self, task_id, title=None, category=None, due_date=None, is_daily=None):
        """Update task details."""
        updates = []
        params = []
        if title:
            updates.append("title = ?")
            params.append(title)
        if category:
            updates.append("category = ?")
            params.append(category)
        if due_date:
            updates.append("due_date = ?")
            params.append(due_date)
        if is_daily is not None:
            updates.append("is_daily = ?")
            params.append(is_daily)
        params.append(task_id)
        query = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
        self.cursor.execute(query, params)
        self.conn.commit()

    def mark_completed(self, task_id):
        """Mark a task as fully completed."""
        self.cursor.execute("UPDATE tasks SET completed = 1 WHERE id = ?", (task_id,))
        self.conn.commit()

    def mark_daily_completed(self, task_id):
        """Mark a task as completed for today."""
        today = date.today().strftime("%Y-%m-%d")
        self.cursor.execute("UPDATE tasks SET daily_completed_date = ? WHERE id = ?", (today, task_id))
        self.conn.commit()

    def reset_daily_completion(self):
        """Reset daily completion for tasks where daily_completed_date is not today."""
        today = date.today().strftime("%Y-%m-%d")
        self.cursor.execute("UPDATE tasks SET daily_completed_date = NULL WHERE daily_completed_date != ? AND is_daily = 1", (today,))
        self.conn.commit()

    def delete_task(self, task_id):
        """Delete a task."""
        self.cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        self.conn.commit()

    def __del__(self):
        """Close database connection."""
        self.conn.close()

# Custom Task Widget
class TaskItem(QWidget):
    def __init__(self, task, parent=None, show_daily_checkbox=False):
        super().__init__(parent)
        self.task = task
        self.task_id, title, category, due_date, completed, created_at, is_daily, daily_completed_date = task
        self.parent_widget = parent
        layout = QHBoxLayout()

        # Checkbox for marking task as fully completed
        self.checkbox = QCheckBox(title)
        self.checkbox.setChecked(bool(completed))
        layout.addWidget(self.checkbox)

        # Daily completion checkbox (only shown in Daily Tasks tab)
        if show_daily_checkbox and is_daily:
            today = date.today().strftime("%Y-%m-%d")
            self.daily_checkbox = QCheckBox("Done Today")
            self.daily_checkbox.setChecked(daily_completed_date == today)
            layout.addWidget(self.daily_checkbox)
            self.daily_checkbox.stateChanged.connect(self.toggle_daily_completion)

        # Labels for category and due date
        category_label = QLabel(category or "No Category")
        due_label = QLabel(due_date or "No Due Date")
        layout.addWidget(category_label)
        layout.addWidget(due_label)

        # Edit and Delete buttons
        edit_btn = QPushButton("Edit")
        edit_btn.setFixedWidth(60)
        edit_btn.clicked.connect(self.edit_task)
        delete_btn = QPushButton("Delete")
        delete_btn.setFixedWidth(60)
        delete_btn.clicked.connect(self.delete_task)
        layout.addWidget(edit_btn)
        layout.addWidget(delete_btn)

        self.setLayout(layout)

    def toggle_daily_completion(self):
        """Toggle daily completion status."""
        if self.daily_checkbox.isChecked():
            self.parent_widget.db.mark_daily_completed(self.task_id)
        else:
            self.parent_widget.db.cursor.execute("UPDATE tasks SET daily_completed_date = NULL WHERE id = ?", (self.task_id,))
            self.parent_widget.db.conn.commit()
        self.parent_widget.refresh_daily_tasks()

    def edit_task(self):
        """Open dialog to edit task."""
        dialog = TaskDialog(self.task, self.parent_widget)
        if dialog.exec_():
            title, category, due_date, is_daily = dialog.get_data()
            self.parent_widget.db.update_task(self.task_id, title, category, due_date, is_daily)
            self.parent_widget.refresh_all()

    def delete_task(self):
        """Delete task with confirmation."""
        reply = QMessageBox.question(self, "Delete Task", "Are you sure you want to delete this task?",
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.parent_widget.db.delete_task(self.task_id)
            self.parent_widget.refresh_all()

# Task Dialog for Adding/Editing Tasks
class TaskDialog(QDialog):
    def __init__(self, task=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Task")
        self.setFixedWidth(300)
        layout = QVBoxLayout()

        # Task input fields
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Task Title")
        self.category_combo = QComboBox()
        self.category_combo.addItems(["Work", "Personal", "Urgent", "Other"])
        self.due_date = QDateEdit()
        self.due_date.setCalendarPopup(True)
        self.due_date.setDate(QDate.currentDate())
        self.is_daily = QCheckBox("Daily Task")

        # Set existing task data if editing
        if task:
            task_id, title, category, due_date, completed, created_at, is_daily, daily_completed_date = task
            self.title_input.setText(title)
            self.category_combo.setCurrentText(category or "Other")
            if due_date:
                self.due_date.setDate(QDate.fromString(due_date, "yyyy-MM-dd"))
            self.is_daily.setChecked(bool(is_daily))

        # Buttons
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        layout.addWidget(QLabel("Task Title:"))
        layout.addWidget(self.title_input)
        layout.addWidget(QLabel("Category:"))
        layout.addWidget(self.category_combo)
        layout.addWidget(QLabel("Due Date:"))
        layout.addWidget(self.due_date)
        layout.addWidget(self.is_daily)
        layout.addWidget(save_btn)

        self.setLayout(layout)

    def get_data(self):
        """Return task data."""
        return (self.title_input.text(), self.category_combo.currentText(),
                self.due_date.date().toString("yyyy-MM-dd"), self.is_daily.isChecked())

# Main Application Window
class ToDoApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("To-Do List App")
        self.setGeometry(100, 100, 800, 600)
        self.setWindowIcon(QIcon("assets/icon.png"))  # Assumed icon path
        self.db = Database()
        self.theme = "light"
        self.init_ui()
        self.apply_stylesheet()
        self.db.reset_daily_completion()  # Reset daily tasks on app start

    def init_ui(self):
        """Initialize the UI with tabs."""
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Tab widgets
        self.home_tab = QWidget()
        self.task_tab = QWidget()
        self.daily_tab = QWidget()
        self.completed_tab = QWidget()
        self.settings_tab = QWidget()

        # Add tabs
        self.tabs.addTab(self.home_tab, "Home")
        self.tabs.addTab(self.task_tab, "Tasks")
        self.tabs.addTab(self.daily_tab, "Daily Tasks")
        self.tabs.addTab(self.completed_tab, "Completed")
        self.tabs.addTab(self.settings_tab, "Settings")

        self.init_home_tab()
        self.init_task_tab()
        self.init_daily_tab()
        self.init_completed_tab()
        self.init_settings_tab()

        # Animation for tab switching
        self.tabs.currentChanged.connect(self.animate_tab_switch)

    def init_home_tab(self):
        """Initialize Home/Dashboard tab."""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        title = QLabel("Welcome to Your To-Do App!")
        title.setFont(QFont("Segoe UI", 20, QFont.Bold))
        stats = QLabel(f"Tasks: {len(self.db.get_tasks(0))} | Daily: {len(self.db.get_tasks(is_daily=1))} | Completed: {len(self.db.get_tasks(1))}")
        stats.setFont(QFont("Segoe UI", 14))
        layout.addWidget(title)
        layout.addWidget(stats)
        self.home_tab.setLayout(layout)

    def init_task_tab(self):
        """Initialize Task List tab."""
        layout = QVBoxLayout()

        # Add task button
        add_btn = QPushButton("Add Task")
        add_btn.clicked.connect(self.add_task)
        layout.addWidget(add_btn)

        # Filter and sort
        filter_layout = QHBoxLayout()
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All", "Work", "Personal", "Urgent", "Other"])
        self.filter_combo.currentTextChanged.connect(self.refresh_tasks)
        sort_btn = QPushButton("Sort by Due Date")
        sort_btn.clicked.connect(self.sort_tasks)
        filter_layout.addWidget(QLabel("Filter by Category:"))
        filter_layout.addWidget(self.filter_combo)
        filter_layout.addWidget(sort_btn)
        layout.addLayout(filter_layout)

        # Task list
        self.task_list = QListWidget()
        layout.addWidget(self.task_list)
        self.task_tab.setLayout(layout)
        self.refresh_tasks()

    def init_daily_tab(self):
        """Initialize Daily Tasks tab."""
        layout = QVBoxLayout()
        self.daily_list = QListWidget()
        layout.addWidget(self.daily_list)
        self.daily_tab.setLayout(layout)
        self.refresh_daily_tasks()

    def init_completed_tab(self):
        """Initialize Completed Tasks tab."""
        layout = QVBoxLayout()
        self.completed_list = QListWidget()
        layout.addWidget(self.completed_list)
        self.completed_tab.setLayout(layout)
        self.refresh_completed_tasks()

    def init_settings_tab(self):
        """Initialize Settings tab."""
        layout = QVBoxLayout()
        theme_btn = QPushButton("Toggle Theme")
        theme_btn.clicked.connect(self.toggle_theme)
        layout.addWidget(theme_btn)
        layout.addStretch()
        self.settings_tab.setLayout(layout)

    def add_task(self):
        """Open dialog to add a new task."""
        dialog = TaskDialog(parent=self)
        if dialog.exec_():
            title, category, due_date, is_daily = dialog.get_data()
            self.db.add_task(title, category, due_date, is_daily)
            self.refresh_all()
            self.animate_task_added()

    def refresh_tasks(self):
        """Refresh task list based on filter."""
        self.task_list.clear()
        category = self.filter_combo.currentText()
        tasks = self.db.get_tasks(0)
        if category != "All":
            tasks = [t for t in tasks if t[2] == category]
        for task in tasks:
            item = QListWidgetItem(self.task_list)
            task_widget = TaskItem(task, self)
            item.setSizeHint(task_widget.sizeHint())
            self.task_list.setItemWidget(item, task_widget)
            task_widget.checkbox.stateChanged.connect(lambda: self.mark_task_completed(task[0]))

    def refresh_daily_tasks(self):
        """Refresh daily tasks list."""
        self.db.reset_daily_completion()  # Reset daily completion status
        self.daily_list.clear()
        tasks = self.db.get_tasks(is_daily=1)
        for task in tasks:
            item = QListWidgetItem(self.daily_list)
            task_widget = TaskItem(task, self, show_daily_checkbox=True)
            item.setSizeHint(task_widget.sizeHint())
            self.daily_list.setItemWidget(item, task_widget)
            task_widget.checkbox.stateChanged.connect(lambda: self.mark_task_completed(task[0]))

    def refresh_completed_tasks(self):
        """Refresh completed tasks list."""
        self.completed_list.clear()
        tasks = self.db.get_tasks(1)
        for task in tasks:
            item = QListWidgetItem(self.completed_list)
            task_widget = TaskItem(task, self)
            item.setSizeHint(task_widget.sizeHint())
            self.completed_list.setItemWidget(item, task_widget)

    def mark_task_completed(self, task_id):
        """Mark task as fully completed and refresh lists."""
        self.db.mark_completed(task_id)
        self.refresh_all()

    def sort_tasks(self):
        """Sort tasks by due date."""
        self.task_list.clear()
        tasks = self.db.get_tasks(0)
        category = self.filter_combo.currentText()
        if category != "All":
            tasks = [t for t in tasks if t[2] == category]
        tasks = sorted(tasks, key=lambda x: x[3] or "9999-12-31")
        for task in tasks:
            item = QListWidgetItem(self.task_list)
            task_widget = TaskItem(task, self)
            item.setSizeHint(task_widget.sizeHint())
            self.task_list.setItemWidget(item, task_widget)
            task_widget.checkbox.stateChanged.connect(lambda: self.mark_task_completed(task[0]))

    def refresh_all(self):
        """Refresh all task lists and home stats."""
        self.refresh_tasks()
        self.refresh_daily_tasks()
        self.refresh_completed_tasks()
        self.update_home_stats()

    def update_home_stats(self):
        """Update stats on home tab."""
        layout = self.home_tab.layout()
        stats = layout.itemAt(1).widget()
        stats.setText(f"Tasks: {len(self.db.get_tasks(0))} | Daily: {len(self.db.get_tasks(is_daily=1))} | Completed: {len(self.db.get_tasks(1))}")

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        self.theme = "dark" if self.theme == "light" else "light"
        self.apply_stylesheet()
        self.animate_theme_transition()

    def apply_stylesheet(self):
        """Apply stylesheet based on theme."""
        if self.theme == "light":
            stylesheet = """
                QWidget {
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 14px;
                }
                QMainWindow {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                                stop:0 #f0f4f8, stop:1 #d9e2ec);
                }
                QPushButton {
                    background-color: #007bff;
                    color: white;
                    border-radius: 5px;
                    padding: 8px;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #0056b3;
                }
                QLineEdit, QComboBox, QDateEdit, QCheckBox {
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    padding: 5px;
                    background-color: #fff;
                }
                QListWidget {
                    background-color: #fff;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                }
                QListWidget::item {
                    padding: 10px;
                    border-bottom: 1px solid #eee;
                }
                QListWidget::item:hover {
                    background-color: #f0f4f8;
                }
                QTabWidget::pane {
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    background-color: #fff;
                }
                QTabWidget::tab {
                    background-color: #e9ecef;
                    padding: 10px;
                    border-radius: 5px 5px 0 0;
                }
                QTabWidget::tab:selected {
                    background-color: #fff;
                    border-bottom: 2px solid #007bff;
                }
            """
        else:
            stylesheet = """
                QWidget {
                    font-family: 'Segoe UI', Arial, sans-serif;
                    font-size: 14px;
                    color: #e0e0e0;
                }
                QMainWindow {
                    background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                                                stop:0 #2c3e50, stop:1 #34495e);
                }
                QPushButton {
                    background-color: #1abc9c;
                    color: white;
                    border-radius: 5px;
                    padding: 8px;
                    margin: 5px;
                }
                QPushButton:hover {
                    background-color: #16a085;
                }
                QLineEdit, QComboBox, QDateEdit, QCheckBox {
                    border: 1px solid #555;
                    border-radius: 5px;
                    padding: 5px;
                    background-color: #34495e;
                    color: #e0e0e0;
                }
                QListWidget {
                    background-color: #34495e;
                    border: 1px solid #555;
                    border-radius: 5px;
                }
                QListWidget::item {
                    padding: 10px;
                    border-bottom: 1px solid #444;
                    color: #e0e0e0;
                }
                QListWidget::item:hover {
                    background-color: #3e5f7a;
                }
                QTabWidget::pane {
                    border: 1px solid #555;
                    border-radius: 5px;
                    background-color: #34495e;
                }
                QTabWidget::tab {
                    background-color: #2c3e50;
                    padding: 10px;
                    border-radius: 5px 5px 0 0;
                    color: #e0e0e0;
                }
                QTabWidget::tab:selected {
                    background-color: #34495e;
                    border-bottom: 2px solid #1abc9c;
                }
            """
        self.setStyleSheet(stylesheet)

    def animate_tab_switch(self):
        """Animate tab transition."""
        animation = QPropertyAnimation(self.tabs, b"geometry")
        animation.setDuration(200)
        animation.setStartValue(self.tabs.geometry().adjusted(10, 0, -10, 0))
        animation.setEndValue(self.tabs.geometry())
        animation.start()

    def animate_task_added(self):
        """Animate task list when a task is added."""
        animation = QPropertyAnimation(self.task_list, b"geometry")
        animation.setDuration(200)
        animation.setStartValue(self.task_list.geometry().adjusted(0, 10, 0, -10))
        animation.setEndValue(self.task_list.geometry())
        animation.start()

    def animate_theme_transition(self):
        """Animate theme change."""
        animation = QPropertyAnimation(self, b"windowOpacity")
        animation.setDuration(300)
        animation.setStartValue(0.8)
        animation.setEndValue(1.0)
        animation.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ToDoApp()
    window.show()
    sys.exit(app.exec_())