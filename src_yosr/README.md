# Wireless Network Optimization Application

This project provides a graphical tool for modeling, solving, and visualizing wireless network optimization problems. The application supports integer and mixed linear programming formulations, enabling optimization of user-to-Access Point (AP) assignments based on priorities, capacities, and optionally energy consumption.

## Table of Contents

- [Features](#features)  
- [Installation](#installation)  
- [Usage](#usage)  
- [Interface Screenshots](#interface-screenshots)  
- [Project Structure](#project-structure)  

## Features

- **User and AP management**: Add, remove, and edit users and APs through intuitive tables.  
- **Global settings**: Configure WiFi band, environment type, and optional energy-aware optimization.  
- **Solver integration**: Optimizations solved using Gurobi via a threaded interface for non-blocking execution.  
- **Visualization**:  
  - Network topology with zoomable graphics  
  - AP coverage areas and interference  
  - User-to-AP assignments with priority and energy information  
- **Intermediate calculations**: Display distance, energy, and interference matrices for analysis.  
- **Predefined test cases**: Load and test scenarios quickly with JSON input files.

## Installation

- clone the repository
 git clone https://github.com/yourusername/wireless-network-optimization.git

- Install dependencies
 pip install -r requirements.txt
- Required packages
 PyQt5
 Gurobi Python API
- Set up Gurobi license Follow the official Gurobi installation instructions for your operating system and ensure your license is active.
- Run the application
 python main.py



## Interface Screenshots

![Main Interface](https://github.com/user-attachments/assets/ed8b3f56-2f01-4f1d-8443-c7512bfd2071)

*Input tables for managing users and access points*

![Input Tables](https://github.com/user-attachments/assets/2efb6538-9dc1-414e-a90c-2d336690ba4b)

*Optimization results and assignment information*


![Visualization](https://github.com/user-attachments/assets/8b802ed7-f3e1-4732-85ae-7f72886d59e4)

*Network topology visualization with coverage areas*

![Results Display](https://github.com/user-attachments/assets/decab091-fc7f-4476-8608-c76354733ab1)

*Intermediate calculations showing distance and energy matrices*


![Calculations](https://github.com/user-attachments/assets/26c27814-5b57-471c-8613-45a61f65f4dc)



## Project Structure
main.py                  - Main GUI entry point  
input_ui.py              - Input interface (users, APs, settings)  
output_ui.py             - Results window  
calculations_ui.py       - Intermediate calculations window  
topology_ui.py           - Network topology visualization  
predefinedExamples_ui.py - Predefined test cases window  
solver_thread.py         - QThread wrapper for solver  
solver.py                - Network optimization logic  
calculations.py          - Preprocessing & intermediate computations  
test_cases/              - JSON test cases  
screenshots/             - Example screenshots for README  
README.md                - Project documentation  


