import sys
from PyQt5.QtWidgets import QTabWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from PyQt5.QtGui import QIcon, QPixmap
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_DIR = os.path.join(BASE_DIR, "icons")


import json
from PyQt5.QtWidgets import (QApplication, QWidget, QVBoxLayout, QHBoxLayout,
                             QTableWidget, QTableWidgetItem, QPushButton, QLabel,
                             QCheckBox, QLineEdit, QFileDialog, QGroupBox, QComboBox,
                             QSpinBox, QTextEdit, QMessageBox)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import gurobipy as gp
from gurobipy import GRB
import networkx as nx
import matplotlib.pyplot as plt

# Defaults

default_arcs = {
    ('A','B'): {'mode':'R','C0':100.0,'c_var':10.0,'c_fix':500.0,'Ymax':200.0},
    ('B','C'): {'mode':'R','C0':80.0,'c_var':12.0,'c_fix':400.0,'Ymax':150.0},
    ('A','C'): {'mode':'F','C0':60.0,'c_var':8.0,'c_fix':300.0,'Ymax':100.0},
    ('C','D'): {'mode':'F','C0':70.0,'c_var':9.0,'c_fix':350.0,'Ymax':120.0},
    ('B','D'): {'mode':'R','C0':50.0,'c_var':20.0,'c_fix':600.0,'Ymax':100.0}
}

default_OD = {
    ('A','D'): {'D':120.0, 'allowed':['R','F'], 'P':500.0},
    ('A','C'): {'D':40.0,  'allowed':['R','F'], 'P':500.0},
    ('B','D'): {'D':30.0,  'allowed':['R'],     'P':500.0}
}

budget_mode_default = {'R':3000.0, 'F':2000.0}

# ---------------------------
# Worker thread (Gurobi)
# ---------------------------
class SolveThread(QThread):
    finished = pyqtSignal(dict)
    status_update = pyqtSignal(str)

    def __init__(self, arcs, OD, nodes, use_budget, budget_R, budget_F, allow_partial, time_limit=None, mip_gap=None):
        super().__init__()
        self.arcs = arcs
        self.OD = OD
        self.nodes = nodes
        self.use_budget = use_budget
        self.budget_R = budget_R
        self.budget_F = budget_F
        self.allow_partial = allow_partial
        self.time_limit = time_limit
        self.mip_gap = mip_gap
        self.model = None
        self._terminate_requested = False

    def request_terminate(self):
        self._terminate_requested = True
        if hasattr(self, 'model') and self.model:
            try:
                self.model.terminate()
                self.status_update.emit('Terminate requested')
            except Exception as e:
                self.status_update.emit(f'Terminate failed: {e}')

    def run(self):
        try:
            self.status_update.emit('Building model...')
            m = gp.Model('PLM_full')
            self.model = m

            y = {}
            z = {}
            u = {}
            f = {}

            # Variables
            for e in self.arcs:
                ymax = float(self.arcs[e].get('Ymax', 1e6))
                y[e] = m.addVar(lb=0, ub=ymax, vtype=GRB.CONTINUOUS, name=f'y_{e[0]}_{e[1]}')
                z[e] = m.addVar(vtype=GRB.BINARY, name=f'z_{e[0]}_{e[1]}')

            for od in self.OD:
                u[od] = m.addVar(lb=0, ub=self.OD[od]['D'], vtype=GRB.CONTINUOUS, name=f'u_{od[0]}_{od[1]}')

            for od in self.OD:
                for e in self.arcs:
                    if self.arcs[e]['mode'] in self.OD[od]['allowed']:
                        f[(od,e)] = m.addVar(lb=0, vtype=GRB.CONTINUOUS, name=f'f_{od[0]}{od[1]}_{e[0]}{e[1]}')

            m.update()

            # Objective

            fixed_cost = gp.quicksum(self.arcs[e]['c_fix'] * z[e] for e in self.arcs)
            var_cost = gp.quicksum(self.arcs[e]['c_var'] * y[e] for e in self.arcs)
            penalty_factor = {}
            for e in self.arcs:
                if self.arcs[e]['mode'] == 'R':  # route
                    penalty_factor[e] = 1.0
                else:  # rail
                    penalty_factor[e] = 2.0  # double penalty

            unsat_cost = gp.quicksum(
                self.OD[od]['P'] * u[od] * max(penalty_factor[e] for e in self.arcs if (od, e) in f)
                for od in self.OD
            )

            m.setObjective(fixed_cost + var_cost + unsat_cost, GRB.MINIMIZE)

            # Flow conservation
            for od in self.OD:
                o,d = od
                for node in self.nodes:
                    expr = gp.LinExpr()
                    for e in self.arcs:
                        if (od,e) in f and e[0] == node:
                            expr += f[(od,e)]
                        if (od,e) in f and e[1] == node:
                            expr -= f[(od,e)]
                    if node == o:
                        if self.allow_partial:
                            m.addConstr(expr == self.OD[od]['D'] - u[od])
                        else:
                            m.addConstr(expr == self.OD[od]['D'])
                    elif node == d:
                        if self.allow_partial:
                            m.addConstr(expr == -(self.OD[od]['D'] - u[od]))
                        else:
                            m.addConstr(expr == -self.OD[od]['D'])
                    else:
                        m.addConstr(expr == 0)

            # Capacities
            for e in self.arcs:
                expr = gp.quicksum(f[(od,e)] for od in self.OD if (od,e) in f)
                m.addConstr(expr <= self.arcs[e]['C0'] + y[e])
                m.addConstr(y[e] <= self.arcs[e]['Ymax'] * z[e])

            # Budgets
            if self.use_budget:
                exprR = gp.quicksum(self.arcs[e]['c_var'] * y[e] + self.arcs[e]['c_fix'] * z[e] for e in self.arcs if self.arcs[e]['mode'] == 'R')
                exprF = gp.quicksum(self.arcs[e]['c_var'] * y[e] + self.arcs[e]['c_fix'] * z[e] for e in self.arcs if self.arcs[e]['mode'] == 'F')
                m.addConstr(exprR <= self.budget_R)
                m.addConstr(exprF <= self.budget_F)

            # Params
            if self.time_limit: m.params.TimeLimit = float(self.time_limit)
            if self.mip_gap: m.params.MIPGap = float(self.mip_gap)
            m.params.OutputFlag = 0

            self.status_update.emit('Optimizing...')
            m.optimize()

            if m.status == GRB.INFEASIBLE:
                self.finished.emit({'error':'Model infeasible'})
                return

            sol = {}
            sol['y'] = {e: y[e].X for e in self.arcs}
            sol['z'] = {e: int(round(z[e].X)) for e in self.arcs}
            sol['u'] = {od: u[od].X for od in self.OD}
            sol['f'] = {k: f[k].X for k in f}
            sol['objective'] = m.ObjVal

            self.finished.emit(sol)
        except Exception as ex:
            self.finished.emit({'error': str(ex)})
        finally:
            self.model = None

# ---------------------------
class PlotWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)

        self.figure = Figure(figsize=(6, 5))
        self.canvas = FigureCanvas(self.figure)

        layout.addWidget(self.canvas)

    def draw_network(self, arcs, OD, sol):
        import networkx as nx

        self.figure.clear()
        ax = self.figure.add_subplot(111)

        G = nx.DiGraph()
        for e in arcs:
            G.add_edge(e[0], e[1])

        pos = nx.spring_layout(G, seed=42)

        flows = sol.get('f', {})
        ys = sol.get('y', {})
        zs = sol.get('z', {})

        for e in G.edges():
            total_flow = sum(flows.get((od, e), 0) for od in OD)
            width = max(1.0, total_flow / 10)

            mode = arcs[e]['mode']
            style = 'solid' if mode == 'R' else 'dotted'

            is_existing = arcs[e]['C0'] > 0
            expanded_or_built = (ys.get(e, 0) > 0 or zs.get(e, 0) > 0)

            if is_existing and expanded_or_built:
                color = '#f2c14e'#blue into yellox
            elif is_existing and not expanded_or_built:
                color = '#f78154'#orange
            elif not is_existing and expanded_or_built:
                color = '#4d9078'#green
            else:
                color = '#b4436c'#purple

            nx.draw_networkx_edges(
                G, pos, edgelist=[e], width=width,
                edge_color=color, style=style, ax=ax
            )

            mid = (
                (pos[e[0]][0] + pos[e[1]][0]) / 2,
                (pos[e[0]][1] + pos[e[1]][1]) / 2
            )
            ax.text(mid[0], mid[1], f"{total_flow:.0f}", color='red', fontsize=9)

        nx.draw_networkx_labels(G, pos, font_size=12, font_weight='bold', ax=ax)

        ax.set_title(
            "\nNetwork Solution\n"

        )
        ax.axis("off")
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], color='#f2c14e', lw=4, label='Existing expanded'),
            Line2D([0], [0], color='#f78154', lw=4, label='Existing not expanded'),
            Line2D([0], [0], color='#4d9078', lw=4, label='New built'),
            Line2D([0], [0], color='#b4436c', lw=4, label='New not built'),
            Line2D([0], [0], color='black', lw=2, linestyle='solid', label='Road'),
            Line2D([0], [0], color='black', lw=2, linestyle='dotted', label='Rail')
        ]
        leg = ax.legend(handles=legend_elements, loc='upper right')
        text_colors = ['#f2c14e', '#f78154', '#4d9078', '#b4436c', 'black', 'black']
        for text, color in zip(leg.get_texts(), text_colors):
            text.set_color(color)


        self.figure.tight_layout(rect=[0, 0, 1, 0.97])
        self.canvas.draw()



# Main GUI
# ---------------------------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('PLM Investissement - Road/Rail')
        self.resize(1000, 700)
        self.tabs = QTabWidget()
        self.main_tab = QWidget()
        self.plot_tab = PlotWidget()

        self.tabs.addTab(self.main_tab, "Main")
        self.tabs.addTab(self.plot_tab, "Plot")

        root_layout = QVBoxLayout(self)
        root_layout.addWidget(self.tabs)

        self.layout = QVBoxLayout()
        self.main_tab.setLayout(self.layout)

        self.arcs = dict(default_arcs)
        self.OD = dict(default_OD)
        self.nodes = sorted(list({n for e in self.arcs for n in e}))
        self.thread = None
        self.last_solution = None

        self._build_ui()

    def icon_label(self, icon_path, text, size=20):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        icon_lbl = QLabel()
        icon_lbl.setPixmap(QPixmap(icon_path).scaled(
            size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))

        text_lbl = QLabel(text)

        layout.addWidget(icon_lbl)
        layout.addWidget(text_lbl)
        layout.addStretch()

        return container

    def _build_ui(self):
        # Apply global style only for main window widgets
        self.setStyleSheet("""
            QWidget#MainTab {
                font-family: 'Segoe UI', sans-serif;
                font-size: 11pt;
                background-color: #fdfdfd;
            }
            QGroupBox {
                border: 1px solid #f4a6b9;       /* beautiful pink border */
                border-radius: 6px;
                margin-top: 10px;
                font-weight: bold;
                padding: 10px;
                background-color: #white;       /* soft light orange */
            }
            QPushButton {
                background-color: #ce4257;        /* beautiful pink */
                color: white;
                border-radius: 5px;
                padding: 6px 12px;
                font-weight: bold;                /* make button text bold */
            }
            QPushButton:hover {
                background-color: #f78154;        /* slightly darker pink on hover */
            }
            QTableWidget {
                background-color: white;        /* orange background inside table */
                gridline-color: #b4436c;          /* pink gridlines */
                border-radius: 5px;
            }
            QHeaderView::section {
                background-color: #ff9b54;        /* light pink headers */
                font-weight: bold;
            }
            QCheckBox, QLabel {
                font-size: 10.5pt;
                color: black;                   /* orange text for labels */
                font-weight: bold;                 /* bold labels */
            }
            QTextEdit {
                background-color: #fff0f5;        /* soft pink log */
                border: 1px solid #4d9078;
                border-radius: 5px;
            }
            QSpinBox, QComboBox {
                border: 1px solid 4d9078;
                border-radius: 4px;
                padding: 2px 4px;
                background-color: #fff0f5;        /* light pink for inputs */
            }
        """)

        # Create a container QWidget with objectName to apply the above style
        self.main_tab.setObjectName("MainTab")

        # JSON buttons + budget
        h = QHBoxLayout()


        btn_load = QPushButton("Charger JSON")
        btn_load.setIcon(QIcon(os.path.join(ICON_DIR, "load.png")))
        btn_load.clicked.connect(self.load_json)
        h.addWidget(btn_load)

        btn_save = QPushButton("Sauvegarder JSON")
        btn_save.setIcon(QIcon(os.path.join(ICON_DIR, "save.png")))
        btn_save.clicked.connect(self.save_json)
        h.addWidget(btn_save)


        self.chk_budget = QCheckBox('Utiliser budgets');
        h.addWidget(self.chk_budget)
        #h.addWidget(QLabel('Budget des voies routières R :'))
        h.addWidget(
            self.icon_label(os.path.join(ICON_DIR, "car.png"), "Budget des voies routières R :")
        )

        self.spin_R = QSpinBox();
        self.spin_R.setRange(0, 10000000);
        self.spin_R.setValue(int(budget_mode_default['R']));
        h.addWidget(self.spin_R)
        #h.addWidget(QLabel('Budget des voies ferroviaires F:'))
        h.addWidget(
            self.icon_label(os.path.join(ICON_DIR, "train.png"), "Budget des voies ferroviaires F :")
        )

        self.spin_F = QSpinBox();
        self.spin_F.setRange(0, 10000000);
        self.spin_F.setValue(int(budget_mode_default['F']));
        h.addWidget(self.spin_F)
        self.layout.addLayout(h)
        self.layout.setSpacing(12)

        # Arc table
        g_arcs = QGroupBox('Arcs (editable)')
        v_arcs = QVBoxLayout();
        g_arcs.setLayout(v_arcs)
        self.arc_table = QTableWidget();
        self.arc_table.setColumnCount(7)
        self.arc_table.setHorizontalHeaderLabels(
            ['From', 'To', 'Capacité Initiale', 'Type', 'Cout par unité', 'Cout fixe', 'Extension Maximale'])
        self.arc_table.horizontalHeader().setStretchLastSection(True)
        v_arcs.addWidget(self.arc_table)
        bar = QHBoxLayout()
        btn_add = QPushButton('Ajouter arc');
        btn_add.clicked.connect(self.add_arc_row);
        bar.addWidget(btn_add)
        btn_rem = QPushButton('Supprimer');
        btn_rem.clicked.connect(self.remove_arc_row);
        bar.addWidget(btn_rem)
        btn_def = QPushButton('Charger par défaut');
        btn_def.clicked.connect(self.load_default);
        bar.addWidget(btn_def)
        v_arcs.addLayout(bar)
        self.layout.addWidget(g_arcs)

        # OD table
        g_od = QGroupBox('OD (editable)')
        v_od = QVBoxLayout();
        g_od.setLayout(v_od)
        self.od_table = QTableWidget();
        self.od_table.setColumnCount(4)
        self.od_table.setHorizontalHeaderLabels(['From', 'To', 'Demande', 'Penalité / Allowed'])
        self.od_table.horizontalHeader().setStretchLastSection(True)
        v_od.addWidget(self.od_table)
        bar2 = QHBoxLayout()
        btn_add_od = QPushButton('Ajouter OD');
        btn_add_od.clicked.connect(self.add_od_row);
        bar2.addWidget(btn_add_od)
        btn_rem_od = QPushButton('Supprimer OD');
        btn_rem_od.clicked.connect(self.remove_od_row);
        bar2.addWidget(btn_rem_od)
        v_od.addLayout(bar2)
        self.layout.addWidget(g_od)

        # Populate tables
        self.load_default()

        # Solve buttons
        h2 = QHBoxLayout()
        self.chk_partial = QCheckBox('Allow partial');
        self.chk_partial.setChecked(True);
        h2.addWidget(self.chk_partial)
        self.btn_solve = QPushButton('Lancer optimisation');
        self.btn_solve.clicked.connect(self.run_solver);
        h2.addWidget(self.btn_solve)
        self.layout.addLayout(h2)

        # Log
        self.log = QTextEdit();
        self.log.setReadOnly(True);
        self.log.setFixedHeight(130)
        self.layout.addWidget(self.log)

    def load_default(self):
        self.arcs = dict(default_arcs)
        self.OD = dict(default_OD)
        self.nodes = sorted(list({n for e in self.arcs for n in e}))
        self.populate_arc_table()
        self.populate_od_table()

    def populate_arc_table(self):
        self.arc_table.setRowCount(len(self.arcs))
        for r, e in enumerate(self.arcs):
            u,v = e
            self.arc_table.setItem(r,0,QTableWidgetItem(u))
            self.arc_table.setItem(r,1,QTableWidgetItem(v))
            self.arc_table.setItem(r,2,QTableWidgetItem(str(self.arcs[e]['C0'])))
            type_cb = QComboBox(); type_cb.addItems(['R','F']); type_cb.setCurrentText(self.arcs[e]['mode']); self.arc_table.setCellWidget(r,3,type_cb)
            self.arc_table.setItem(r,4,QTableWidgetItem(str(self.arcs[e]['c_var'])))
            self.arc_table.setItem(r,5,QTableWidgetItem(str(self.arcs[e]['c_fix'])))
            self.arc_table.setItem(r,6,QTableWidgetItem(str(self.arcs[e]['Ymax'])))

    def populate_od_table(self):
        self.od_table.setRowCount(len(self.OD))
        for r, od in enumerate(self.OD):
            o,d = od
            self.od_table.setItem(r,0,QTableWidgetItem(o))
            self.od_table.setItem(r,1,QTableWidgetItem(d))
            self.od_table.setItem(r,2,QTableWidgetItem(str(self.OD[od]['D'])))
            self.od_table.setItem(r,3,QTableWidgetItem(f"{self.OD[od]['P']} / {','.join(self.OD[od]['allowed'])}"))

    def add_arc_row(self):
        r = self.arc_table.rowCount(); self.arc_table.insertRow(r)
        self.arc_table.setItem(r,0,QTableWidgetItem('X'))
        self.arc_table.setItem(r,1,QTableWidgetItem('Y'))
        self.arc_table.setItem(r,2,QTableWidgetItem('0'))
        cb = QComboBox(); cb.addItems(['R','F']); self.arc_table.setCellWidget(r,3,cb)
        self.arc_table.setItem(r,4,QTableWidgetItem('0'))
        self.arc_table.setItem(r,5,QTableWidgetItem('0'))
        self.arc_table.setItem(r,6,QTableWidgetItem('100'))

    def remove_arc_row(self):
        rows = sorted(set(idx.row() for idx in self.arc_table.selectedIndexes()), reverse=True)
        for r in rows: self.arc_table.removeRow(r)

    def add_od_row(self):
        r = self.od_table.rowCount(); self.od_table.insertRow(r)
        self.od_table.setItem(r,0,QTableWidgetItem('O'))
        self.od_table.setItem(r,1,QTableWidgetItem('D'))
        self.od_table.setItem(r,2,QTableWidgetItem('0'))
        self.od_table.setItem(r,3,QTableWidgetItem('1000 / R,F'))

    def remove_od_row(self):
        rows = sorted(set(idx.row() for idx in self.od_table.selectedIndexes()), reverse=True)
        for r in rows: self.od_table.removeRow(r)

    def read_tables(self):
        arcs = {}
        for r in range(self.arc_table.rowCount()):
            u = self.arc_table.item(r,0).text()
            v = self.arc_table.item(r,1).text()
            try: C0 = float(self.arc_table.item(r,2).text())
            except: C0 = 0.0
            cb = self.arc_table.cellWidget(r,3)
            mode = cb.currentText() if cb else 'R'
            try: cvar = float(self.arc_table.item(r,4).text())
            except: cvar = 0.0
            try: cfix = float(self.arc_table.item(r,5).text())
            except: cfix = 0.0
            try: ymax = float(self.arc_table.item(r,6).text())
            except: ymax = 100.0
            arcs[(u,v)] = {'mode':mode,'C0':C0,'c_var':cvar,'c_fix':cfix,'Ymax':ymax}
        OD = {}
        for r in range(self.od_table.rowCount()):
            o = self.od_table.item(r,0).text()
            d = self.od_table.item(r,1).text()
            try: D = float(self.od_table.item(r,2).text())
            except: D = 0.0
            txt = self.od_table.item(r,3).text()

            P = 1000.0; allowed=['R','F']
            if '/' in txt:
                left,right = txt.split('/',1)
                try: P=float(left.strip())
                except: P=1000.0
                allowed=[s.strip().upper() for s in right.split(',')]
            OD[(o,d)] = {'D':D,'P':P,'allowed':allowed}
        return arcs, OD


    def run_solver(self):
        self.arcs, self.OD = self.read_tables()
        self.nodes = sorted(list({n for e in self.arcs for n in e}))
        use_budget = self.chk_budget.isChecked()
        budget_R = self.spin_R.value()
        budget_F = self.spin_F.value()
        allow_partial = self.chk_partial.isChecked()
        self.thread = SolveThread(self.arcs, self.OD, self.nodes, use_budget, budget_R, budget_F, allow_partial)
        self.thread.finished.connect(self.show_solution)
        self.thread.status_update.connect(lambda s: self.log.append(s))
        self.thread.start()
        self.log.append("Solver started...")

    def show_solution(self, sol):
        if 'error' in sol:
            QMessageBox.critical(self, 'Solver Error', sol['error'])
            return

        self.last_solution = sol

        # ----------------------------
        # 1) Calcul des composantes
        # ----------------------------

        # Pénalités de demande insatisfaite
        penalty_cost = 0.0
        for od in self.OD:
            unmet = sol['u'].get(od, 0)
            P = self.OD[od]['P']

            # facteur pénalité (R=1, F=2)
            factors = []
            for e in self.arcs:
                if self.arcs[e]['mode'] in self.OD[od]['allowed']:
                    factors.append(1 if self.arcs[e]['mode'] == 'R' else 2)

            factor = min(factors) if factors else 1
            penalty_cost += unmet * P * factor

        # Coûts d’investissement
        invest_cost = sum(
            self.arcs[e]['c_fix'] * sol['z'].get(e, 0)
            for e in self.arcs
        )

        # Coûts d’exploitation (extension)
        operating_cost = sum(
            self.arcs[e]['c_var'] * sol['y'].get(e, 0)
            for e in self.arcs
        )

        total_obj = sol['objective']

        # ----------------------------
        # 2) Construction du résumé
        # ----------------------------
        summary = f"""
        <h2 style="color:#b4436c;">Résumé de la solution optimale</h2>
        <hr>

        <p style="font-size:14px;">
        <b>Valeur de l’objectif total :</b>
        <span style="color:#b4436c; font-size:16px;">
        {total_obj:,.0f}
        </span>
        </p>

        <h3 style="color:#34495e;">🧮 Décomposition de l’objectif</h3>
        <ul>
          <li>
            <span style="color:#b4436c;">
            <b>Pénalités de demande insatisfaite :</b> {penalty_cost:,.0f}
            </span>
          </li>
          <li>
            <span style="color:#4d9078;">
            <b>Coûts d’investissement :</b> {invest_cost:,.0f}
            </span>
          </li>
          <li>
            <span style="color:#f78154;">
            <b>Coûts d’exploitation :</b> {operating_cost:,.0f}
            </span>
          </li>
        </ul>

        <h3 style="color:#34495e;">🚫 Demande non satisfaite</h3>
        <ul>
        """
        for od in self.OD:
            unmet = sol['u'].get(od, 0)
            demand = self.OD[od]['D']
            percent = (unmet / demand * 100) if demand > 0 else 0

            # couleur selon gravité
            if percent == 0:
                color = "#4d9078"  # vert
                icon = "✅"
            elif percent < 50:
                color = "#f78154"  # orange
                icon = "⚠️"
            else:
                color = "#b4436c"  # rouge
                icon = "🚫"

            summary += f"""
            <li>
              <span style="color:{color};">
              {icon} <b>{od[0]} → {od[1]}</b> :
              {unmet:.0f} / {demand:.0f} ({percent:.0f}%)
              </span>
            </li>
            """
        summary += """
        </ul>
        <hr>
        <p style="font-style:italic; color:#555;">
        La valeur élevée de l’objectif est principalement due aux pénalités de demande non satisfaite,
        indiquant une capacité insuffisante du réseau existant.
        </p>
        """
        msg = QMessageBox(self)
        msg.setWindowTitle("Solution Summary")
        msg.setIcon(QMessageBox.Information)
        msg.setTextFormat(Qt.RichText)  # 🔴 TRÈS IMPORTANT
        msg.setText(summary)
        msg.exec()

        #summary = ""
        #summary += "📊 RÉSUMÉ DE LA SOLUTION OPTIMALE\n"
        #summary += "──────────────────────────────\n"
        #summary += f"Valeur de l’objectif total : {total_obj:,.0f}\n\n"

        #summary += "🧮 Décomposition de l’objectif :\n"
        #summary += f"• Pénalités de demande insatisfaite : {penalty_cost:,.0f}\n"
        #summary += f"• Coûts d’investissement : {invest_cost:,.0f}\n"
        #summary += f"• Coûts d’exploitation : {operating_cost:,.0f}\n\n"

        #summary += "🚫 Demande non satisfaite :\n"
        #for od in self.OD:
        #    unmet = sol['u'].get(od, 0)
        #    demand = self.OD[od]['D']
        #   percent = (unmet / demand * 100) if demand > 0 else 0
        #    summary += (
        #        f"• {od[0]} → {od[1]} : "
        #        f"{unmet:.0f} / {demand:.0f} ({percent:.0f}%)\n"
        #    )

        # ----------------------------
        # 3) Affichage
        # ----------------------------
        #QMessageBox.information(self, "Solution Summary", summary)

        #Mise à jour du graphe
        self.plot_tab.draw_network(self.arcs, self.OD, sol)
        self.tabs.setCurrentWidget(self.plot_tab)



    def load_json(self):
        fname, _ = QFileDialog.getOpenFileName(self, 'Open JSON', '', 'JSON Files (*.json)')
        if fname:
            try:
                with open(fname, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                # Convert string keys back to tuple keys
                self.arcs = {tuple(k.split('->')): v for k, v in data.get('arcs', {}).items()}
                self.OD = {tuple(k.split('->')): v for k, v in data.get('OD', {}).items()}

                # Optionally read budgets if present
                if 'budget_R' in data:
                    self.spin_R.setValue(int(data['budget_R']))
                if 'budget_F' in data:
                    self.spin_F.setValue(int(data['budget_F']))

                # Populate tables (just use your normal functions)
                self.populate_arc_table()
                self.populate_od_table()

                self.log.append(f"Loaded JSON from {fname}")

            except Exception as e:
                QMessageBox.critical(self, 'Error', 'Failed to load JSON:\n' + str(e))

    def save_json(self):
        arcs, OD = self.read_tables()

        # Convert tuple keys to strings for JSON
        arcs_json = {f"{k[0]}->{k[1]}": v for k, v in arcs.items()}
        OD_json = {f"{k[0]}->{k[1]}": v for k, v in OD.items()}

        data = {
            'arcs': arcs_json,
            'OD': OD_json,
            'budget_R': self.spin_R.value(),
            'budget_F': self.spin_F.value()
        }

        fname, _ = QFileDialog.getSaveFileName(self, 'Save JSON', '', 'JSON Files (*.json)')
        if fname:
            try:
                with open(fname, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2)
                self.log.append(f"Saved JSON to {fname}")
            except Exception as e:
                QMessageBox.critical(self, 'Error', 'Failed to save JSON:\n' + str(e))






# ---------------------------
# Run
# ---------------------------
if __name__=='__main__':
   app = QApplication(sys.argv)
   win = MainWindow()
   win.show()
   sys.exit(app.exec_())