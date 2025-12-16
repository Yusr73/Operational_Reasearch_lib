from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QLabel, QGroupBox, QHeaderView
)
from PyQt5.QtCore import Qt

class CalculationsWindow(QWidget):
    def __init__(self, intermediates):
        super().__init__()
        self.setWindowTitle("Intermediate Calculations")
        self.showMaximized()  # Fullscreen mode

        layout = QVBoxLayout(self)

        # === Title ===
        title = QLabel("Intermediate Results")
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #283593; margin-bottom: 16px;")
        layout.addWidget(title)

        # === Reconstruct priority groups from weights ===
        U_H = [u for u, weight in intermediates["w"].items() if weight == 3]
        U_M = [u for u, weight in intermediates["w"].items() if weight == 2]
        U_L = [u for u, weight in intermediates["w"].items() if weight == 1]

        # === Summary Table ===
        summary_items = [
            ("Maximum AP range", intermediates["D_max"]),
            ("AP interference radius", intermediates["D_intf"]),
            ("High Priority Users", ", ".join(U_H)),
            ("Medium Priority Users", ", ".join(U_M)),
            ("Low Priority Users", ", ".join(U_L))
        ]

        summary_table = QTableWidget()
        summary_table.setColumnCount(2)
        summary_table.setRowCount(len(summary_items))
        summary_table.setHorizontalHeaderLabels(["Metric", "Value"])
        summary_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        summary_table.verticalHeader().setVisible(False)
        summary_table.setStyleSheet(self.table_style())  # fixed here

        for row, (metric, value) in enumerate(summary_items):
            summary_table.setItem(row, 0, QTableWidgetItem(metric))
            summary_table.setItem(row, 1, QTableWidgetItem(str(value)))

        layout.addWidget(summary_table)

        # === Subtables in pairs ===
        row1 = QHBoxLayout()
        row1.addWidget(self.make_table("Feasible Edges ", intermediates["E"], ["User", "AP"]))
        row1.addWidget(self.make_table("Distances", intermediates["distances"], ["(User, AP)", "Distance"]))
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(self.make_table("Energy Costs ", intermediates["c"], ["(User, AP)", "Cost"]))
        row2.addWidget(self.make_table("Interference Pairs ", intermediates["I"], ["AP1", "AP2"]))
        layout.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addStretch()
        row3.addWidget(self.make_table("Maximum combined users", intermediates["M"], ["(AP1, AP2)", "M_ab"]))
        row3.addStretch()
        layout.addLayout(row3)

        self.setLayout(layout)

    # === Add these two methods ===
    def table_style(self):
        return """
            QTableWidget {
                background-color: #f9f9f9;
                border: 1px solid #b39ddb;
                border-radius: 8px;
                font-family: Roboto;
                font-size: 13px;
            }
            QHeaderView::section {
                background-color: #5c6bc0;
                color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
        """

    def make_table(self, title, data, headers):
        box = QGroupBox(title)
        box_layout = QVBoxLayout(box)

        table = QTableWidget()
        table.setColumnCount(2)
        table.setHorizontalHeaderLabels(headers)
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        table.verticalHeader().setVisible(False)
        table.setStyleSheet(self.table_style())

        if isinstance(data, dict):
            table.setRowCount(len(data))
            for row, (key, value) in enumerate(data.items()):
                table.setItem(row, 0, QTableWidgetItem(str(key)))
                table.setItem(row, 1, QTableWidgetItem(str(round(value, 2) if isinstance(value, float) else value)))
        elif isinstance(data, list):
            table.setRowCount(len(data))
            for row, item in enumerate(data):
                if isinstance(item, tuple) and len(item) == 2:
                    table.setItem(row, 0, QTableWidgetItem(str(item[0])))
                    table.setItem(row, 1, QTableWidgetItem(str(item[1])))
                else:
                    table.setItem(row, 0, QTableWidgetItem(str(item)))
                    table.setItem(row, 1, QTableWidgetItem(""))
        else:
            table.setRowCount(1)
            table.setItem(0, 0, QTableWidgetItem(str(data)))
            table.setItem(0, 1, QTableWidgetItem(""))

        box_layout.addWidget(table)
        return box
