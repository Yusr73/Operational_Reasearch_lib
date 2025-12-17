# -*- coding: utf-8 -*-
"""
Created on Wed Dec 17 05:56:28 2025

@author: msi
"""

import sys
import os
from PyQt5.QtWidgets import QMainWindow

project_dir = os.path.dirname(__file__)
sys.path.insert(0, project_dir)

# CHANGE THIS LINE:
# Replace 'your_filename' with your actual Python filename (without .py)
# Replace 'YourWindowClassName' with your actual window class name
from src.main_window import MainWindow as TargetWindow

class LaunchWindow(TargetWindow):
    pass