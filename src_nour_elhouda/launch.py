import sys
import os
from PyQt5.QtWidgets import QMainWindow

project_dir = os.path.dirname(_file_)
sys.path.insert(0, project_dir)

# CHANGE THIS LINE:
# Replace 'your_filename' with your actual Python filename (without .py)
# Replace 'YourWindowClassName' with your actual window class name
from main_window.py import MainWindow as TargetWindow

class LaunchWindow(TargetWindow):
    pass