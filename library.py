import sys
import os
import importlib.util
from src_nour.main import MainWindow #nour


# Get the base directory
base_dir = os.path.dirname(__file__)

# Add your src_yosr/src to the path
src_yosr_path = os.path.join(base_dir, 'src_yosr', 'src')
if os.path.exists(src_yosr_path):
    sys.path.insert(0, src_yosr_path)

# Import your NetworkGUI
try:
    from input_ui import NetworkGUI
except ImportError:
    try:
        alt_path = os.path.join(base_dir, 'src_yosr')
        sys.path.insert(0, alt_path)
        from src.input_ui import NetworkGUI
    except ImportError:
        NetworkGUI = None

from PyQt5.QtWidgets import (
    QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QApplication, QSpacerItem, QSizePolicy, QGraphicsView,
    QGraphicsScene, QGraphicsTextItem, QMessageBox
)
from PyQt5.QtGui import QPixmap, QFont, QColor
from PyQt5.QtCore import Qt, QTimer


class ORLibraryWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Operational Research Problems Library")
        self.showMaximized()

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(30)

        # === Cover Photo ===
        self.cover = QLabel()
        self.cover.setAlignment(Qt.AlignCenter)
        self.cover.setStyleSheet("background: transparent; border: none;")

        base_dir = os.path.dirname(__file__)
        cover_path = os.path.join(base_dir, "src_yosr", "screenshots", "cover.png")

        cover_pixmap = QPixmap(cover_path)
        self.cover.setPixmap(cover_pixmap.scaled(
            self.screen().size().width(), 220,
            Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation
        ))
        self.cover.setFixedHeight(220)
        layout.addWidget(self.cover)

        # === Sparkling Title ===
        self.view = QGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.view.setStyleSheet("background: transparent; border: none;")
        layout.addWidget(self.view)

        self.title_item = QGraphicsTextItem("Operational Research Problems Library")
        font = QFont("Lucida Handwriting", 36, QFont.Bold)

        self.title_item.setFont(font)
        self.title_item.setDefaultTextColor(QColor("#2e7d32"))
        self.scene.addItem(self.title_item)

        rect = self.title_item.boundingRect()
        self.title_item.setPos((self.screen().size().width() - rect.width()) / 2, 30)

        # Animate glow
        self.colors = [
            QColor("#0d47a1"),
            QColor("#1565c0"),
            QColor("#1976d2"),
            QColor("#1e88e5"),
            QColor("#2196f3"),
            QColor("#42a5f5"),
            QColor("#64b5f6"),
            QColor("#90caf9"),
        ]
        self.color_index = 0

        self.title_item.setDefaultTextColor(self.colors[0])

        self.timer = QTimer()
        self.timer.timeout.connect(self.animate_glow)
        self.timer.start(200)

        # === Buttons Section ===
        button_row = QHBoxLayout()
        button_row.setSpacing(50)

        labels_text = [
            "Planning of road and railway routes to be added.",
            "Assign connections without interference.",
            "Optimization of fund transfers between banks/currencies.",
            "Determine the minimal number of monitoring nodes required.",
            "Problem 5: description here"
        ]

        # Project mappings - each person uses their folder name
        self.project_mappings = {
            1: {"folder": "src_nour", "class_name": "MainWindow", "file": "launch"},
            2: {"folder": "src_yosr", "class_name": "NetworkGUI", "file": "input_ui"},
            3: {"folder": "src_nour_elhouda", "class_name": "MainWindow", "file": "launch"},
            4: {"folder": "src_adem", "class_name": "MainWindow", "file": "launch"},
            5: {"folder": "src_slim", "class_name": "MainWindow", "file": "launch"}
        }

        for i in range(5):
            box = QVBoxLayout()
            box.setSpacing(30)

            icon = QLabel()
            base_dir = os.path.dirname(__file__)
            icon_path = os.path.join(base_dir, "src_yosr", "screenshots", f"problem{i + 1}.png")

            pixmap = QPixmap(icon_path)
            if not pixmap.isNull():
                icon.setPixmap(pixmap.scaled(80, 80, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            icon.setAlignment(Qt.AlignCenter)
            icon.setStyleSheet("background: transparent; border: none;")
            box.addWidget(icon)

            btn = QPushButton(f"Problem {i + 1}")
            btn.setFixedSize(180, 55)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1976d2;
                    color: white;
                    font-weight: bold;
                    border-radius: 16px;
                    font-size: 20px;
                    font-family: Garamond;
                }
                QPushButton:hover {
                    background-color: #1565c0;
                }
            """)
            box.addWidget(btn, alignment=Qt.AlignCenter)

            # Connect button
            from functools import partial
            btn.clicked.connect(partial(self.launch_project, i + 1))

            label = QLabel(labels_text[i])
            label.setAlignment(Qt.AlignCenter)
            label.setWordWrap(True)
            label.setFont(QFont("Garamond", 16, QFont.Normal))
            label.setStyleSheet("""
                QLabel {
                    color: #2c3e50;
                    background-color: rgba(255, 255, 255, 180);
                    border-radius: 8px;
                    padding: 6px 10px;
                }
            """)
            box.addWidget(label)

            button_row.addLayout(box)

        layout.addSpacerItem(QSpacerItem(20, 100, QSizePolicy.Minimum, QSizePolicy.Expanding))
        layout.addLayout(button_row)
        layout.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))

    def animate_glow(self):
        self.title_item.setDefaultTextColor(self.colors[self.color_index])
        self.color_index = (self.color_index + 1) % len(self.colors)

    def launch_project(self, problem_num):
        """Launch the project GUI."""
        #Problem 1 button
        if problem_num == 1:
            try:
                from src_nour.main import MainWindow  # Import the class directly from main.py
                self.nour_window = MainWindow()       # Create instance
                self.nour_window.show()               # Show GUI
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Cannot open Project 1:\n{str(e)}")
            return

        


        
        # Your button (Problem 2)
        if problem_num == 2:
            try:
                if NetworkGUI is None:
                    QMessageBox.critical(self, "Error", "NetworkGUI not available")
                    return
                self.network_window = NetworkGUI()
                self.network_window.show()
                return
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Cannot open:\n{str(e)}")
                return

        # For others (Nour, Nour_Elhouda, Adem, Slim)
        mapping = self.project_mappings.get(problem_num)
        if not mapping:
            QMessageBox.warning(self, "Error", f"No project found for Problem {problem_num}")
            return

        folder = mapping["folder"]
        class_name = mapping["class_name"]
        file_name = mapping["file"]

        base_dir = os.path.dirname(__file__)
        project_dir = os.path.join(base_dir, folder)
        module_path = os.path.join(project_dir, f"{file_name}.py")

        # Check if project exists
        if not os.path.exists(module_path):
            QMessageBox.warning(
                self,
                "Project Not Ready",
                f"Project for Problem {problem_num} is not set up yet.\n\n"
                f"Expected: {folder}/{file_name}.py"
            )
            return

        try:
            # Add project directory to path
            if project_dir not in sys.path:
                sys.path.insert(0, project_dir)

            # Load the module
            spec = importlib.util.spec_from_file_location(file_name, module_path)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Get the MainWindow class
            window_class = getattr(module, class_name, None)
            if window_class is None:
                QMessageBox.warning(
                    self,
                    "Setup Error",
                    f"File {file_name}.py must contain: class MainWindow(QMainWindow)"
                )
                return

            # Create and show window
            # Store as instance variable to prevent garbage collection
            window_instance = window_class()
            
            # Store reference based on problem number
            if problem_num == 1:
                self.nour_window = window_instance
            elif problem_num == 3:
                self.nour_elhouda_window = window_instance
            elif problem_num == 4:
                self.adem_window = window_instance
            elif problem_num == 5:
                self.slim_window = window_instance
            
            window_instance.show()

        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Cannot launch project {problem_num}:\n{str(e)}"
            )


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ORLibraryWindow()
    window.show()
    sys.exit(app.exec_())
