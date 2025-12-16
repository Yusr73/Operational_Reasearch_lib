from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QPushButton, QHBoxLayout, QLabel, QMessageBox
from PyQt5.QtCore import Qt
from calculations_ui import CalculationsWindow
from calculations import compute_intermediates
from topology import TopologyWindow


class OutputWindow(QWidget):
    def __init__(self, users, aps, settings, assignments=None, messages=None):
        super().__init__()
        self.setWindowTitle("Optimization Result")
        self.setFixedSize(700, 500)

        self.users = users
        self.aps = aps
        self.settings = settings

        # === Ensure assignments is a dict with all APs as keys ===
        if assignments is None:
            assignments = {a["Name"]: [] for a in aps}
        else:
            # Fill missing APs with empty lists
            for a in aps:
                if a["Name"] not in assignments:
                    assignments[a["Name"]] = []
            # Ensure all values are lists
            for k, v in assignments.items():
                if not isinstance(v, list):
                    assignments[k] = []
        self.assignments = assignments

        layout = QVBoxLayout(self)

        # === Styled Table ===
        self.table = QTableWidget()
        self.table.setColumnCount(2)
        self.table.setHorizontalHeaderLabels(["Access Point", "Assigned Users"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #f3e5f5;
                border: 2px solid #7e57c2;
                border-radius: 12px;
                font-family: Roboto;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1565c0, stop:1 #ab47bc);
                color: white;
                font-weight: bold;
                padding: 8px;
                border: none;
            }
            QTableWidget::item { padding: 6px; }
        """)
        self.table.setRowCount(len(self.assignments))
        for row, (ap, users_list) in enumerate(self.assignments.items()):
            ap_item = QTableWidgetItem(ap)
            ap_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 0, ap_item)

            # Safe: ensure users_list is a list
            if not isinstance(users_list, list):
                users_list = []
            users_item = QTableWidgetItem(", ".join(users_list))
            users_item.setTextAlignment(Qt.AlignCenter)
            self.table.setItem(row, 1, users_item)

        layout.addWidget(self.table)

        # === Solver messages area ===
        self.message_label = QLabel()
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.message_label.setStyleSheet("""
            QLabel {
                background-color: #f9f9ff;
                border: 1px solid #b39ddb;
                border-radius: 10px;
                padding: 8px;
                font-family: Roboto;
                font-size: 13px;
                color: #283593;
            }
        """)
        self.message_label.setMinimumHeight(80)
        layout.addWidget(self.message_label)

        if messages:
            self.set_solver_messages(messages)

        # === Buttons ===
        button_layout = QHBoxLayout()
        self.intermediate_btn = QPushButton("Show Intermediate Calculations")
        self.intermediate_btn.setStyleSheet(self.button_style())
        self.intermediate_btn.clicked.connect(self.show_intermediates)

        self.topology_btn = QPushButton("Show Topology")
        self.topology_btn.setStyleSheet(self.button_style())
        self.topology_btn.clicked.connect(self.show_topology)

        button_layout.addWidget(self.intermediate_btn)
        button_layout.addWidget(self.topology_btn)
        layout.addLayout(button_layout)

    def button_style(self):
        return """
            QPushButton {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1565c0, stop:1 #ab47bc);
                color: white;
                font-size: 15px;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 14px;
            }
            QPushButton:hover { background-color: #6a1b9a; }
        """

    def show_intermediates(self):
        try:
            intermediates = compute_intermediates(self.users, self.aps, self.settings)
            self.calculations_window = CalculationsWindow(intermediates)
            self.calculations_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Intermediate calculation failed:\n{e}")

    def show_topology(self):
        try:
            if not isinstance(self.assignments, dict):
                raise ValueError("Assignments not available or invalid.")

            intermediates = compute_intermediates(self.users, self.aps, self.settings)
            self.topology_window = TopologyWindow(self.users, self.aps, self.assignments, intermediates)
            self.topology_window.show()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Topology failed:\n{e}")

    # === Message API ===
    def set_solver_messages(self, messages):
        if isinstance(messages, (list, tuple)):
            text = "\n".join(f"• {msg}" for msg in messages)
        else:
            text = str(messages)
        self.message_label.setText(text)

    def append_solver_message(self, message):
        current = self.message_label.text().strip()
        bullet = f"• {message}"
        self.message_label.setText(current + ("\n" if current else "") + bullet)
