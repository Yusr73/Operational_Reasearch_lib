from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QTableWidget, QTableWidgetItem, QPushButton,
    QComboBox, QCheckBox, QLineEdit, QSpinBox,
    QSizePolicy, QSpacerItem, QHeaderView, QMessageBox
)
from PyQt5.QtGui import QFont, QPixmap, QIntValidator
from PyQt5.QtCore import Qt
from calculations import compute_intermediates
from output_ui import OutputWindow
from solver_thread import SolverThread  # QThread wrapper for the solver


class NetworkGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.device_combos = []
        self.setWindowTitle("Wireless Network Optimization")
        self.setWindowState(Qt.WindowMaximized)
        self.setFont(QFont("Roboto", 11))

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        layout.setContentsMargins(40, 20, 40, 20)
        layout.setSpacing(20)
        central.setLayout(layout)

        # --- TOP SECTION ---
        top = QHBoxLayout()
        top.setSpacing(40)
        layout.addLayout(top)

        # --- USER SECTION ---
        user_layout = QVBoxLayout()
        user_layout.setSpacing(12)

        self.user_icon = QLabel()
        self.user_icon.setFixedSize(160, 160)
        self.user_icon.setAlignment(Qt.AlignCenter)
        self.user_icon.setPixmap(
            QPixmap(r"C:/Bureau/Documenten/RT3/Info/Recherche operationnelle/project/ro-matching/src_yosr/screenshots/Copilot_20251127_214136-removebg-preview.png")
            .scaled(160, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        user_layout.addWidget(self.user_icon, alignment=Qt.AlignCenter)

        user_label = QLabel("Users Table")
        user_label.setAlignment(Qt.AlignCenter)
        user_label.setStyleSheet(
            "QLabel { font-size: 16px; font-weight: bold; color: #283593; margin-bottom: 6px; }"
        )
        user_layout.addWidget(user_label)

        self.user_table = QTableWidget(0, 5)
        self.user_table.setHorizontalHeaderLabels(["Name", "Priority", "X", "Y", "Device type"])
        self.user_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.user_table.verticalHeader().setVisible(False)
        self.user_table.setStyleSheet("""
            QTableWidget { background-color: #e8eaf6; font-family: Roboto; border: 1px solid #7e57c2; }
            QHeaderView::section { background-color: #5c6bc0; color: white; font-weight: bold; padding: 6px; }
        """)
        user_layout.addWidget(self.user_table)

        user_buttons = QHBoxLayout()
        self.add_user_btn = QPushButton("Add User")
        self.add_user_btn.setStyleSheet(self.green_button())
        self.remove_user_btn = QPushButton("Remove Last User")
        self.remove_user_btn.setStyleSheet(self.red_button())
        user_buttons.addWidget(self.add_user_btn)
        user_buttons.addWidget(self.remove_user_btn)
        user_layout.addLayout(user_buttons)
        top.addLayout(user_layout)

        # --- AP SECTION ---
        ap_layout = QVBoxLayout()
        ap_layout.setSpacing(12)

        self.ap_icon = QLabel()
        self.ap_icon.setFixedSize(160, 160)
        self.ap_icon.setAlignment(Qt.AlignCenter)
        self.ap_icon.setPixmap(
            QPixmap(r"C:\Bureau\Documenten\RT3\Info\Recherche operationnelle\project\ro-matching\src_yosr\screenshots\image-removebg-preview.png")
            .scaled(160, 160, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )
        ap_layout.addWidget(self.ap_icon, alignment=Qt.AlignCenter)

        ap_label = QLabel("Access Points Table")
        ap_label.setAlignment(Qt.AlignCenter)
        ap_label.setStyleSheet(
            "QLabel { font-size: 16px; font-weight: bold; color: #283593; margin-bottom: 6px; }"
        )
        ap_layout.addWidget(ap_label)

        self.ap_table = QTableWidget(0, 5)
        self.ap_table.setHorizontalHeaderLabels(["Name", "Capacity", "Channel", "X", "Y"])
        self.ap_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.ap_table.verticalHeader().setVisible(False)
        self.ap_table.setStyleSheet("""
            QTableWidget { background-color: #e8eaf6; font-family: Roboto; border: 1px solid #5c6bc0; }
            QHeaderView::section { background-color: #5c6bc0; color: white; font-weight: bold; padding: 6px; }
        """)
        ap_layout.addWidget(self.ap_table)

        ap_buttons = QHBoxLayout()
        self.add_ap_btn = QPushButton("Add AP")
        self.add_ap_btn.setStyleSheet(self.green_button())
        self.remove_ap_btn = QPushButton("Remove Last AP")
        self.remove_ap_btn.setStyleSheet(self.red_button())
        ap_buttons.addWidget(self.add_ap_btn)
        ap_buttons.addWidget(self.remove_ap_btn)
        ap_layout.addLayout(ap_buttons)
        top.addLayout(ap_layout)

        # --- SETTINGS SECTION ---
        settings_layout = QHBoxLayout()
        settings_layout.setSpacing(16)

        wifi_label = QLabel("WiFi Band:")
        wifi_label.setStyleSheet("QLabel { color: #283593; font-weight: 600; }")
        self.wifi_band = QComboBox()
        self.wifi_band.addItems(["2.4 GHz", "5 GHz"])
        self.wifi_band.setStyleSheet(self.dropdown_style())

        env_label = QLabel("Environment Type:")
        env_label.setStyleSheet("QLabel { color: #283593; font-weight: 600; }")
        self.env_type = QComboBox()
        self.env_type.addItems(["Indoor","Urban", "Outdoor"])
        self.env_type.setStyleSheet(self.dropdown_style())

        self.power_checkbox = QCheckBox("Include Power Consumption in Optimization")
        self.power_checkbox.setStyleSheet("""
            QCheckBox { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #a5d6a7, stop:1 #66bb6a);
                        color: white; padding: 6px 10px; border-radius: 14px; font-weight: bold; }
            QCheckBox::indicator { width: 18px; height: 18px; border-radius: 10px; border: 1px solid #2e7d32; background: white; }
            QCheckBox::indicator:checked { background: #2e7d32; }
        """)
        self.power_checkbox.stateChanged.connect(self.toggle_device_combos)
        self.power_checkbox.setChecked(False)

        self.calculate_btn = QPushButton("Calculate")
        self.calculate_btn.setStyleSheet("""
            QPushButton { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1565c0, stop:1 #ab47bc); color: white; font-size: 16px;
                    font-weight: bold; padding: 10px 20px; border-radius: 18px; }
            QPushButton:hover { background-color: #6a1b9a; }
        """)
        self.test_examples_btn = QPushButton("Test predefined examples")
        self.test_examples_btn.setStyleSheet("""
            QPushButton { background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #1565c0, stop:1 #ab47bc); color: white; font-size: 16px;
                    font-weight: bold; padding: 10px 20px; border-radius: 14px; }
            QPushButton:hover { background-color: #6a1b9a; }
        """)

        settings_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        settings_layout.addWidget(wifi_label)
        settings_layout.addWidget(self.wifi_band)
        settings_layout.addWidget(env_label)
        settings_layout.addWidget(self.env_type)
        settings_layout.addWidget(self.power_checkbox)
        settings_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        settings_layout.addWidget(self.calculate_btn)
        settings_layout.addWidget(self.test_examples_btn)
        settings_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))

        layout.addLayout(settings_layout)

        # --- Connections ---
        self.add_user_btn.clicked.connect(self.add_user_row)
        self.remove_user_btn.clicked.connect(self.remove_user_row)
        self.add_ap_btn.clicked.connect(self.add_ap_row)
        self.remove_ap_btn.clicked.connect(self.remove_ap_row)
        self.calculate_btn.clicked.connect(self.run_solver)
        self.test_examples_btn.clicked.connect(self.open_test_cases_window)

    # --- Styles ---
    def green_button(self):
        return "QPushButton { background-color: #4caf50; color: white; border: none; border-radius: 12px; padding: 8px 16px; font-weight: bold; } QPushButton:hover { background-color: #388e3c; }"

    def red_button(self):
        return "QPushButton { background-color: #f44336; color: white; border: none; border-radius: 12px; padding: 8px 16px; font-weight: bold; } QPushButton:hover { background-color: #d32f2f; }"

    def dropdown_style(self):
        return "QComboBox { background-color: #ffffff; border: 1px solid #90caf9; border-radius: 10px; padding: 6px 8px; min-width: 140px; } QComboBox QAbstractItemView { background-color: #ffffff; border: 1px solid #90caf9; selection-background-color: #bbdefb; }"

    # --- Table logic ---
    def add_user_row(self):
        row = self.user_table.rowCount()
        self.user_table.insertRow(row)
        self.user_table.setCellWidget(row, 0, QLineEdit())
        priority_combo = QComboBox()
        priority_combo.addItems(["Low", "Medium", "High"])
        self.user_table.setCellWidget(row, 1, priority_combo)
        x_edit = QLineEdit()
        x_edit.setValidator(QIntValidator())
        self.user_table.setCellWidget(row, 2, x_edit)
        y_edit = QLineEdit()
        y_edit.setValidator(QIntValidator())
        self.user_table.setCellWidget(row, 3, y_edit)
        device_combo = QComboBox()
        device_combo.addItems(["IoT Sensor", "Wearable", "Smartphone", "Tablet", "Laptop"])
        device_combo.setEnabled(self.power_checkbox.isChecked())
        self.user_table.setCellWidget(row, 4, device_combo)
        self.device_combos.append(device_combo)

    def remove_user_row(self):
        row = self.user_table.rowCount()
        if row > 0:
            self.user_table.removeRow(row - 1)
            self.device_combos.pop()

    def add_ap_row(self):
        row = self.ap_table.rowCount()
        self.ap_table.insertRow(row)
        self.ap_table.setCellWidget(row, 0, QLineEdit())
        self.ap_table.setCellWidget(row, 1, QSpinBox())
        self.ap_table.setCellWidget(row, 2, QSpinBox())
        x_edit = QLineEdit()
        x_edit.setValidator(QIntValidator())
        self.ap_table.setCellWidget(row, 3, x_edit)
        y_edit = QLineEdit()
        y_edit.setValidator(QIntValidator())
        self.ap_table.setCellWidget(row, 4, y_edit)

    def remove_ap_row(self):
        row = self.ap_table.rowCount()
        if row > 0:
            self.ap_table.removeRow(row - 1)

    def toggle_device_combos(self, state):
        enabled = state == Qt.Checked
        for combo in self.device_combos:
            combo.setEnabled(enabled)

    # --- Save/load tables ---
    def save_user_table(self):
        users_data = []
        for row in range(self.user_table.rowCount()):
            name = self.user_table.cellWidget(row, 0).text()
            priority = self.user_table.cellWidget(row, 1).currentText()
            x_text = self.user_table.cellWidget(row, 2).text()
            y_text = self.user_table.cellWidget(row, 3).text()
            device = self.user_table.cellWidget(row, 4).currentText()
            users_data.append({
                "Name": name,
                "Priority": priority,
                "X": int(x_text) if x_text else None,
                "Y": int(y_text) if y_text else None,
                "Device": device
            })
        return users_data

    def save_ap_table(self):
        aps_data = []
        for row in range(self.ap_table.rowCount()):
            name = self.ap_table.cellWidget(row, 0).text()
            capacity = self.ap_table.cellWidget(row, 1).value()
            channel = self.ap_table.cellWidget(row, 2).value()
            x_text = self.ap_table.cellWidget(row, 3).text()
            y_text = self.ap_table.cellWidget(row, 4).text()
            aps_data.append({
                "Name": name,
                "Capacity": capacity,
                "Channel": channel,
                "X": int(x_text) if x_text else None,
                "Y": int(y_text) if y_text else None
            })
        return aps_data

    def get_global_settings(self):
        return {
            "WifiBand": self.wifi_band.currentText(),
            "EnvironmentType": self.env_type.currentText(),
            "IncludePowerConsumption": self.power_checkbox.isChecked()
        }

    # --- Solver integration ---
    def run_solver(self):
        users = self.save_user_table()
        aps = self.save_ap_table()
        settings = self.get_global_settings()
        self.calculate_btn.setEnabled(False)

        self.solver_thread = SolverThread(users, aps, settings)
        self.solver_thread.result_ready.connect(
            lambda assignments, status, intermediates: self.on_solver_finished(assignments, status, intermediates, users, aps, settings)
        )
        self.solver_thread.error.connect(self.on_solver_error)
        self.solver_thread.start()

    def on_solver_finished(self, assignments, status, intermediates, users, aps, settings):
        self.calculate_btn.setEnabled(True)
        total_connected = sum(len(u_list) for u_list in assignments.values())
        total_users = len(users)
        if total_connected > 0:
            avg_priority = sum(intermediates['w'][u] for u_list in assignments.values() for u in u_list) / total_connected
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

    def on_solver_error(self, error_msg):
        self.calculate_btn.setEnabled(True)
        QMessageBox.critical(self, "Solver Error", error_msg)

    # --- Test cases ---
    def open_test_cases_window(self):
        from test_cases_ui import TestCasesWindow
        self.test_cases_window = TestCasesWindow()
        self.test_cases_window.show()
