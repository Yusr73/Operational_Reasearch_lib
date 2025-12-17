# src_nour/launch.py
import sys
import os

# Ensure project directory is in sys.path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Import your real MainWindow from main.py
from main import MainWindow as YourMainWindow

# Wrapper class for library import
class MainWindow(YourMainWindow):
    pass


# Optional: run standalone for testing
def start_gui():
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    start_gui()
