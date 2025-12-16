import os, json, sys, subprocess
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton,
    QMessageBox, QScrollArea, QFrame
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from calculations import compute_intermediates
from output_ui import OutputWindow
from solver_thread import SolverThread  # threaded solver wrapper


class TestCasesWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Predefined Test Cases")
        self.setFixedSize(700, 500)
        self.setFont(QFont("Roboto", 11))

        layout = QVBoxLayout(self)

        # Title
        title = QLabel("Predefined Examples")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet(
            "QLabel { font-size: 18px; font-weight: bold; color: #283593; margin-bottom: 12px; }"
        )
        layout.addWidget(title)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        self.list_layout = QVBoxLayout(container)
        scroll.setWidget(container)
        container.setStyleSheet("QWidget { background-color: #f3e5f5; border-radius: 12px; }")
        layout.addWidget(scroll)

        # Populate test cases
        self.populate_test_cases()

    def button_style(self):
        return """
            QPushButton { background-color: #ab47bc; color: white; font-size: 14px;
                          font-weight: bold; padding: 6px 14px; border-radius: 12px; }
            QPushButton:hover { background-color: #8e24aa; }
        """

    def populate_test_cases(self):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        test_dir = os.path.join(base_dir, "test_cases")

        if not os.path.exists(test_dir):
            QMessageBox.critical(self, "Error", f"Folder not found:\n{test_dir}")
            return

        files = [f for f in os.listdir(test_dir) if f.endswith(".json")]
        if not files:
            QMessageBox.information(self, "Info", "No JSON test cases found.")
            return

        for fname in files:
            fpath = os.path.join(test_dir, fname)

            row = QFrame()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(6, 6, 6, 6)

            label = QLabel(fname)
            label.setStyleSheet("QLabel { font-size: 14px; color: #283593; }")
            row_layout.addWidget(label)

            see_btn = QPushButton("See source")
            see_btn.setStyleSheet(self.button_style())
            see_btn.clicked.connect(lambda _, p=fpath: self.open_in_editor(p))
            row_layout.addWidget(see_btn)

            test_btn = QPushButton("Test")
            test_btn.setStyleSheet(self.button_style())
            test_btn.clicked.connect(lambda _, p=fpath: self.run_test_case_threaded(p))
            row_layout.addWidget(test_btn)

            self.list_layout.addWidget(row)

        self.list_layout.addStretch()

    def open_in_editor(self, file_path):
        try:
            if sys.platform.startswith("win"):
                os.startfile(file_path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", file_path])
            else:
                subprocess.Popen(["xdg-open", file_path])
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Cannot open file:\n{e}")

    # --- Threaded execution ---
    def run_test_case_threaded(self, file_path):
        try:
            users, aps, settings = self.load_scenario(file_path)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load scenario:\n{e}")
            return

        self.solver_thread = SolverThread(users, aps, settings)
        self.solver_thread.result_ready.connect(
            lambda assignments, status, intermediates:
            self.on_solver_finished(users, aps, settings, assignments, status, intermediates)
        )
        self.solver_thread.error.connect(lambda msg: QMessageBox.critical(self, "Solver Error", msg))
        self.solver_thread.start()

    def on_solver_finished(self, users, aps, settings, assignments, status, intermediates):
        total_connected = sum(len(u_list) for u_list in assignments.values())
        total_users = len(users)

        if total_connected > 0:
            avg_priority = sum(
                intermediates['w'][u] for u_list in assignments.values() for u in u_list
            ) / total_connected
            messages = [
                f"Status: {status}",
                f"Total users connected: {total_connected}/{total_users}",
                f"Average priority of connected users: {avg_priority:.2f}"
            ]
        else:
            messages = [
                f"Status: {status}",
                f"Total users connected: {total_connected}/{total_users}",
                "Average priority cannot be computed (no users connected)."
            ]

        self.output_window = OutputWindow(users, aps, settings, assignments, messages=messages)
        self.output_window.show()

    def load_scenario(self, file_path):
        """Load and validate JSON scenario file."""
        with open(file_path, "r") as f:
            data = json.load(f)

        if not all(k in data for k in ("users", "aps", "settings")):
            raise ValueError("JSON must contain 'users', 'aps', and 'settings' keys.")

        users = data["users"]
        aps = data["aps"]
        settings = data["settings"]

        if not isinstance(users, list) or not isinstance(aps, list) or not isinstance(settings, dict):
            raise ValueError("Invalid JSON structure.")

        return users, aps, settings
