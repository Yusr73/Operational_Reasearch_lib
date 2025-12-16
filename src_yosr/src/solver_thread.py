from PyQt5.QtCore import QThread, pyqtSignal
from solver import solve_network
from calculations import compute_intermediates

class SolverThread(QThread):
    result_ready = pyqtSignal(object, object, object)  # assignments, status, intermediates
    error = pyqtSignal(str)

    def __init__(self, users, aps, settings):
        super().__init__()
        self.users = users
        self.aps = aps
        self.settings = settings

    def run(self):
        try:
            intermediates = compute_intermediates(self.users, self.aps, self.settings)
            assignments, status = solve_network(intermediates, self.aps)

            # Ensure assignments is always a dict
            if assignments is None or not isinstance(assignments, dict):
                assignments = {a["Name"]: [] for a in self.aps}
            else:
                for a in self.aps:
                    if a["Name"] not in assignments or not isinstance(assignments[a["Name"]], list):
                        assignments[a["Name"]] = []

            self.result_ready.emit(assignments, status, intermediates)
        except Exception as e:
            self.error.emit(str(e))
