# Operational Research Problems Library

This is a centralized library application that connects multiple operational research problem solutions into one interface. Each team member's project can be launched from a single dashboard in `library.py`.

## Project Structure

```
Operational_Reasearch_lib/
├── library.py              # Main dashboard application
├── src_yosr/              # Problem 2: Network Assignment (Yosr)
├── src_adem/              # Problem 4: Vertex Cover (Adem) ✓
├── src_nour/              # Problem 1: Planning of road and railway routes(Nour)
├── src_nour_elhouda/      # Problem 3: (Nour Elhouda)
└── src_slim/              # Problem 5: (Slim)
```

## Problems

1. **Problem 1**: Planning of road and railway routes
2. **Problem 2**: Assign connections without interference (Yosr) ✓
3. **Problem 3**: Optimization of fund transfers between banks/currencies
4. **Problem 4**: Determine the minimal number of monitoring nodes required (Adem) ✓
5. **Problem 5**: Description here

## Installation

### Prerequisites
- Python 3.8+
- PyQt5
- Additional dependencies per project (see individual requirements.txt)

### Setup
```bash
# Install dependencies for all projects
pip install -r src_yosr/requirements.txt
pip install -r src_adem/requirements.txt
# Add others as needed
```

## Running the Library

Launch the main dashboard:
```bash
cd Operational_Reasearch_lib
python3 library.py
```

Click on any problem button to launch the corresponding application.

## Individual Projects

Each project can also be run standalone:

### Problem 2 (Yosr)
```bash
cd src_yosr/src
python3 main.py
```

### Problem 4 (Adem)
```bash
cd src_adem
python3 main.py
```

## Integration Guide for New Projects

To integrate a new project:

1. Create your folder (e.g., `src_yourname/`)
2. Create `launch.py` in your folder:
   ```python
   import sys
   import os
   
   project_dir = os.path.dirname(os.path.abspath(__file__))
   if project_dir not in sys.path:
       sys.path.insert(0, project_dir)
   
   from your_module import YourMainWindow
   
   class MainWindow(YourMainWindow):
       pass
   ```
3. Update `library.py` problem mappings
4. Add your problem icon to `src_yosr/screenshots/`

## Testing

Test your integration:
```bash
python3 test_adem_integration.py
```

## Contributors
- Nour: Problem 1 (Planning of road and railway routes)
- Yosr: Problem 2 (Network Assignment)
- Adem: Problem 4 (Surveillance Network / Vertex Cover)
- [Add other contributors]
