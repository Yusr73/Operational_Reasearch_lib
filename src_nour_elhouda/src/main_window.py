# src/main_window.py
"""
Fenêtre principale de l'application avec interface graphique complète.
Gère la saisie des données, la résolution et la visualisation.
"""

import sys
import json
import os
from datetime import datetime
from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTabWidget, QTableWidget, QTableWidgetItem, QPushButton,
                            QLabel, QLineEdit, QSpinBox, QDoubleSpinBox, QComboBox,
                            QGroupBox, QFormLayout, QTextEdit, QMessageBox, QFileDialog,
                            QSplitter, QProgressBar, QHeaderView, QCheckBox, QDialog,
                            QDialogButtonBox, QMenu, QScrollArea, QFrame, QSizePolicy)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QSize
from PyQt6.QtGui import QFont, QPalette, QColor, QIcon
from gurobi_thread import GurobiThread
from visualization import visualize_network, plot_results_comparison
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import networkx as nx
import pandas as pd
import numpy as np

class NetworkInputDialog(QDialog):
    """Dialogue pour la saisie des nœuds et arcs du réseau"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuration du Réseau Financier")
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        # Formulaire pour les nœuds
        node_group = QGroupBox("Banques/Comptes (Nœuds)")
        node_layout = QFormLayout()
        
        self.node_count = QSpinBox()
        self.node_count.setRange(2, 20)
        self.node_count.setValue(5)
        node_layout.addRow("Nombre de nœuds:", self.node_count)
        
        self.node_names = QTextEdit()
        self.node_names.setPlaceholderText("Entrez un nom par ligne\nFormat recommandé: Nom_DEVISE\nExemple:\nBNP_EUR\nSG_USD\nHSBC_GBP\nDeutsche_EUR\nJPMorgan_USD\n💡 Le suffixe après '_' définit la devise")
        self.node_names.setMaximumHeight(100)
        node_layout.addRow("Noms des nœuds:", self.node_names)
        
        node_group.setLayout(node_layout)
        layout.addWidget(node_group)
        
        # Formulaire pour les arcs
        arc_group = QGroupBox("Transferts Possibles (Arcs)")
        arc_layout = QVBoxLayout()
        
        self.arc_table = QTableWidget(0, 4)
        self.arc_table.setHorizontalHeaderLabels(["Source", "Destination", "Coût (%)", "Capacité Max"])
        # Permettre le redimensionnement des colonnes
        header = self.arc_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionsMovable(True)
        
        arc_layout.addWidget(self.arc_table)
        
        btn_layout = QHBoxLayout()
        add_btn = QPushButton("Ajouter un arc")
        add_btn.clicked.connect(self.add_arc_row)
        remove_btn = QPushButton("Supprimer l'arc sélectionné")
        remove_btn.clicked.connect(self.remove_arc_row)
        btn_layout.addWidget(add_btn)
        btn_layout.addWidget(remove_btn)
        arc_layout.addLayout(btn_layout)
        
        arc_group.setLayout(arc_layout)
        layout.addWidget(arc_group)
        
        # Boutons de dialogue
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | 
                                     QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
        
        # Initialiser quelques arcs par défaut
        self.initialize_default_arcs()
    
    def initialize_default_arcs(self):
        """Initialise quelques arcs par défaut pour faciliter les tests"""
        self.arc_table.setRowCount(3)
        
        # Arc 1
        self.arc_table.setItem(0, 0, QTableWidgetItem("BNP_EUR"))
        self.arc_table.setItem(0, 1, QTableWidgetItem("SG_USD"))
        self.arc_table.setItem(0, 2, QTableWidgetItem("1.5"))
        self.arc_table.setItem(0, 3, QTableWidgetItem("1000000"))
        
        # Arc 2
        self.arc_table.setItem(1, 0, QTableWidgetItem("SG_USD"))
        self.arc_table.setItem(1, 1, QTableWidgetItem("HSBC_GBP"))
        self.arc_table.setItem(1, 2, QTableWidgetItem("2.0"))
        self.arc_table.setItem(1, 3, QTableWidgetItem("500000"))
        
        # Arc 3
        self.arc_table.setItem(2, 0, QTableWidgetItem("HSBC_GBP"))
        self.arc_table.setItem(2, 1, QTableWidgetItem("JPMorgan_USD"))
        self.arc_table.setItem(2, 2, QTableWidgetItem("1.0"))
        self.arc_table.setItem(2, 3, QTableWidgetItem("750000"))
    
    def add_arc_row(self):
        """Ajoute une nouvelle ligne pour un arc"""
        row = self.arc_table.rowCount()
        self.arc_table.insertRow(row)
    
    def remove_arc_row(self):
        """Supprime la ligne sélectionnée"""
        current_row = self.arc_table.currentRow()
        if current_row >= 0:
            self.arc_table.removeRow(current_row)
    
    def get_network_data(self):
        """Récupère les données du réseau saisies"""
        # Récupérer les noms des nœuds
        node_text = self.node_names.toPlainText().strip()
        if node_text:
            nodes = [n.strip() for n in node_text.split('\n') if n.strip()]
        else:
            nodes = [f"Banque_{i}" for i in range(self.node_count.value())]
        
        # Récupérer les arcs
        arcs = []
        for row in range(self.arc_table.rowCount()):
            source_item = self.arc_table.item(row, 0)
            dest_item = self.arc_table.item(row, 1)
            cost_item = self.arc_table.item(row, 2)
            cap_item = self.arc_table.item(row, 3)
            
            if (source_item and dest_item and 
                cost_item and cap_item):
                arcs.append({
                    'source': source_item.text(),
                    'destination': dest_item.text(),
                    'cost': float(cost_item.text()),
                    'capacity': float(cap_item.text())
                })
        
        return {'nodes': nodes, 'arcs': arcs}


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""
    
    # Signaux
    solution_ready = pyqtSignal(dict)
    solving_started = pyqtSignal()
    solving_finished = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.network_data = None
        self.supply_demand = {}
        self.results = None
        self.init_ui()
        self.setup_connections()
        
        # Charger des données d'exemple
        self.load_sample_data()
    
    def init_ui(self):
        """Initialise l'interface utilisateur"""
        self.setWindowTitle("Système d'Optimisation des Transferts Financiers - Flux à Coût Minimum")
        self.setGeometry(100, 50, 1400, 900)
        
        # Widget central avec défilement
        central_widget = QWidget()
        scroll_area = QScrollArea()
        scroll_area.setWidget(central_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setCentralWidget(scroll_area)
        
        # Layout principal avec espacement augmenté
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(15)  # Plus d'espace entre les éléments
        main_layout.setContentsMargins(20, 20, 20, 20)  # Marges augmentées
        
        # Barre d'outils
        toolbar_layout = QHBoxLayout()
        
        self.configure_btn = QPushButton("Configurer le Réseau")
        self.configure_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        
        self.solve_btn = QPushButton("Résoudre l'Optimisation")
        self.solve_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
        """)
        
        self.export_btn = QPushButton("Exporter les Résultats")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #e68a00;
            }
        """)

        self.test_btn = QPushButton("Charger Test")
        self.test_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                font-weight: bold;
                padding: 8px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        
        toolbar_layout.addWidget(self.configure_btn)
        toolbar_layout.addWidget(self.test_btn)
        toolbar_layout.addWidget(self.solve_btn)
        toolbar_layout.addWidget(self.export_btn)
        toolbar_layout.addStretch()
        
        main_layout.addLayout(toolbar_layout)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Zone de contenu avec onglets
        self.tab_widget = QTabWidget()
        self.tab_widget.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 10px;
            }
            QTabBar::tab {
                padding: 8px 16px;
                margin-right: 2px;
                border-radius: 3px;
            }
            QTabBar::tab:selected {
                background-color: #2196F3;
                color: white;
            }
            QTabBar::tab:!selected {
                background-color: #f0f0f0;
            }
        """)
        
        # Onglet 1: Saisie des données (avec défilement)
        self.data_tab = self.create_data_tab()
        self.tab_widget.addTab(self.data_tab, "📊 Données du Réseau")
        
        # Onglet 2: Résultats
        self.results_tab = self.create_results_tab()
        self.tab_widget.addTab(self.results_tab, "📈 Résultats")
        
        # Onglet 3: Visualisation
        self.viz_tab = self.create_viz_tab()
        self.tab_widget.addTab(self.viz_tab, "📊 Visualisation")
        
        # Onglet 4: Analyse
        self.analysis_tab = self.create_analysis_tab()
        self.tab_widget.addTab(self.analysis_tab, "🔍 Analyse")
        
        main_layout.addWidget(self.tab_widget)
        
        # Zone de statut
        self.status_label = QLabel("Prêt")
        self.statusBar().addWidget(self.status_label)
        
        # Appliquer le style
        self.apply_stylesheet()
    
    def create_data_tab(self):
        """Crée l'onglet de saisie des données avec défilement"""
        # Widget principal avec défilement
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(15)
        scroll_layout.setContentsMargins(10, 10, 10, 10)
        
        # Créer un widget pour le contenu principal
        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(15)
        layout.setContentsMargins(10, 10, 10, 10)
    
        # Section d'information du réseau
        info_group = QGroupBox("Information du Réseau")
        info_layout = QFormLayout()
        info_layout.setSpacing(10)
    
        self.network_info_label = QLabel("Aucun réseau configuré")
        info_layout.addRow("État:", self.network_info_label)
    
        # Label pour le résumé des devises
        self.currency_summary_label = QLabel("")
        self.currency_summary_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                font-weight: bold;
                padding: 8px;
                background-color: #f8f9fa;
                border-radius: 4px;
                border: 1px solid #dee2e6;
            }
        """)
        info_layout.addRow("Devises:", self.currency_summary_label)
    
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
    
        # Table des nœuds (offre/demande)
        nodes_group = QGroupBox("Banques/Comptes - Offre et Demande")
        nodes_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        nodes_layout = QVBoxLayout()
    
        self.nodes_table = QTableWidget(0, 4)
        self.nodes_table.setHorizontalHeaderLabels([
            "Banque/Compte", 
            "Devise", 
            "Type", 
            "Valeur (€)"
        ])
    
        # Configuration de la table des nœuds - Permettre le redimensionnement
        header = self.nodes_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionsMovable(True)
        header.setStretchLastSection(True)
        
        # Largeurs initiales
        header.setMinimumSectionSize(80)
        self.nodes_table.setColumnWidth(0, 200)  # Banque/Compte
        self.nodes_table.setColumnWidth(1, 80)   # Devise
        self.nodes_table.setColumnWidth(2, 100)  # Type
        self.nodes_table.setColumnWidth(3, 120)  # Valeur
    
        self.nodes_table.setAlternatingRowColors(True)
        self.nodes_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.nodes_table.setMinimumHeight(200)
        self.nodes_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
        nodes_layout.addWidget(self.nodes_table)
    
        # Boutons pour les nœuds
        node_buttons_layout = QHBoxLayout()
    
        add_node_btn = QPushButton("+ Ajouter Nœud")
        add_node_btn.clicked.connect(self.add_node_row)
        add_node_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
    
        remove_node_btn = QPushButton("- Supprimer Nœud")
        remove_node_btn.clicked.connect(self.remove_node_row)
        remove_node_btn.setStyleSheet("""
            QPushButton {
                background-color: #dc3545;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #c82333;
            }
        """)
    
        node_buttons_layout.addWidget(add_node_btn)
        node_buttons_layout.addWidget(remove_node_btn)
        node_buttons_layout.addStretch()
    
        nodes_layout.addLayout(node_buttons_layout)
    
        nodes_group.setLayout(nodes_layout)
        layout.addWidget(nodes_group)
    
        # Table des arcs (coûts et capacités)
        arcs_group = QGroupBox("Transferts Disponibles - Coûts et Capacités")
        arcs_group.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        arcs_layout = QVBoxLayout()
    
        self.arcs_table = QTableWidget(0, 7)
        self.arcs_table.setHorizontalHeaderLabels([
            "Source", 
            "Devise Source", 
            "Destination", 
            "Devise Dest",
            "Coût (%)", 
            "Capacité Max (€)", 
            "Actif"
        ])
    
        # Configuration de la table des arcs - Permettre le redimensionnement
        header = self.arcs_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionsMovable(True)
        header.setStretchLastSection(True)
        
        # Largeurs initiales
        header.setMinimumSectionSize(60)
        self.arcs_table.setColumnWidth(0, 150)  # Source
        self.arcs_table.setColumnWidth(1, 80)   # Devise Source
        self.arcs_table.setColumnWidth(2, 150)  # Destination
        self.arcs_table.setColumnWidth(3, 80)   # Devise Dest
        self.arcs_table.setColumnWidth(4, 80)   # Coût
        self.arcs_table.setColumnWidth(5, 120)  # Capacité
        self.arcs_table.setColumnWidth(6, 60)   # Actif
    
        self.arcs_table.setAlternatingRowColors(True)
        self.arcs_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.arcs_table.setMinimumHeight(250)
        self.arcs_table.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
    
        arcs_layout.addWidget(self.arcs_table)
    
        # Boutons pour les arcs
        arc_buttons_layout = QHBoxLayout()
    
        add_arc_btn = QPushButton("+ Ajouter Arc")
        add_arc_btn.clicked.connect(self.add_arc_row)
        add_arc_btn.setStyleSheet("""
            QPushButton {
                background-color: #007bff;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #0069d9;
            }
        """)
    
        remove_arc_btn = QPushButton("- Supprimer Arc")
        remove_arc_btn.clicked.connect(self.remove_arc_row)
        remove_arc_btn.setStyleSheet("""
            QPushButton {
                background-color: #ffc107;
                color: #212529;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #e0a800;
            }
        """)
    
        auto_fill_btn = QPushButton("🔄 Remplir Automatiquement")
        auto_fill_btn.clicked.connect(self.auto_fill_arcs)
        auto_fill_btn.setToolTip("Crée automatiquement des arcs entre toutes les combinaisons de nœuds")
        auto_fill_btn.setStyleSheet("""
            QPushButton {
                background-color: #6f42c1;
                color: white;
                font-weight: bold;
                padding: 8px 15px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #5a32a3;
            }
        """)
    
        arc_buttons_layout.addWidget(add_arc_btn)
        arc_buttons_layout.addWidget(remove_arc_btn)
        arc_buttons_layout.addWidget(auto_fill_btn)
        arc_buttons_layout.addStretch()
    
        arcs_layout.addLayout(arc_buttons_layout)
    
        # Info sur les transferts inter-devises
        inter_currency_info = QLabel("💡 Les transferts inter-devises sont surlignés en jaune")
        inter_currency_info.setStyleSheet("""
            QLabel {
                color: #856404;
                background-color: #fff3cd;
                padding: 8px;
                border-radius: 4px;
                border: 1px solid #ffeaa7;
            }
        """)
        arcs_layout.addWidget(inter_currency_info)
    
        arcs_group.setLayout(arcs_layout)
        layout.addWidget(arcs_group)
    
        # Options avancées
        advanced_group = QGroupBox("Options Avancées d'Optimisation")
        advanced_layout = QFormLayout()
        advanced_layout.setSpacing(10)
    
        # Option 1: Risque de change
        self.risk_checkbox = QCheckBox("Inclure le risque de change")
        self.risk_checkbox.setToolTip("Ajoute une majoration de 10-20% aux transferts entre devises différentes")
        self.risk_checkbox.setStyleSheet("""
            QCheckBox {
                font-weight: bold;
                padding: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QCheckBox::indicator:checked {
                background-color: #28a745;
            }
        """)
    
        # Option 2: Multi-devises
        self.multi_currency_checkbox = QCheckBox("Optimisation multi-devises")
        self.multi_currency_checkbox.setToolTip("Optimise les transferts en tenant compte des conversions de devises")
        self.multi_currency_checkbox.setStyleSheet("""
            QCheckBox {
                font-weight: bold;
                padding: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QCheckBox::indicator:checked {
                background-color: #17a2b8;
            }
        """)
    
        # Option 3: Contraintes de temps
        self.time_constraint_checkbox = QCheckBox("Contraintes de temps")
        self.time_constraint_checkbox.setToolTip("Limite la longueur des chemins de transfert (max 2-3 intermédiaires)")
        self.time_constraint_checkbox.setStyleSheet("""
            QCheckBox {
                font-weight: bold;
                padding: 8px;
            }
            QCheckBox::indicator {
                width: 20px;
                height: 20px;
            }
            QCheckBox::indicator:checked {
                background-color: #ffc107;
            }
        """)
    
        advanced_layout.addRow("📊 Gestion des Devises:", self.risk_checkbox)
        advanced_layout.addRow("🌍 Optimisation:", self.multi_currency_checkbox)
        advanced_layout.addRow("⏱️ Contraintes:", self.time_constraint_checkbox)
    
        # Info sur les options
        options_info = QLabel("💡 Les options modifient les coûts et influencent l'optimisation")
        options_info.setStyleSheet("""
            QLabel {
                color: #0c5460;
                background-color: #d1ecf1;
                padding: 10px;
                border-radius: 4px;
                border: 1px solid #bee5eb;
                font-size: 10pt;
            }
        """)
        advanced_layout.addRow("", options_info)
    
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
    
        # Section de vérification
        verification_group = QGroupBox("Vérification des Données")
        verification_layout = QVBoxLayout()
    
        self.verification_text = QTextEdit()
        self.verification_text.setReadOnly(True)
        self.verification_text.setMaximumHeight(120)
        self.verification_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #ced4da;
                border-radius: 4px;
                font-family: 'Courier New', monospace;
                font-size: 9pt;
                padding: 5px;
            }
        """)
        verification_layout.addWidget(self.verification_text)
    
        verify_btn = QPushButton("✅ Vérifier la Cohérence")
        verify_btn.clicked.connect(self.verify_data_consistency)
        verify_btn.setStyleSheet("""
            QPushButton {
                background-color: #20c997;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 4px;
                font-size: 10pt;
            }
            QPushButton:hover {
                background-color: #1aa179;
            }
        """)
        verification_layout.addWidget(verify_btn)
    
        verification_group.setLayout(verification_layout)
        layout.addWidget(verification_group)
    
        layout.addStretch()
        
        # Ajouter le widget de contenu au layout de défilement
        scroll_layout.addWidget(content_widget)
        
        return scroll_widget
    
    def create_results_tab(self):
        """Crée l'onglet des résultats"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Résumé des résultats
        summary_group = QGroupBox("Résumé de l'Optimisation")
        summary_layout = QFormLayout()
        
        self.objective_label = QLabel("N/A")
        self.solving_time_label = QLabel("N/A")
        self.status_label_results = QLabel("N/A")
        
        summary_layout.addRow("Valeur optimale:", self.objective_label)
        summary_layout.addRow("Temps de résolution:", self.solving_time_label)
        summary_layout.addRow("Statut:", self.status_label_results)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Table des flux optimaux
        flows_group = QGroupBox("Flux Optimaux de Transfert")
        flows_layout = QVBoxLayout()
        
        self.flows_table = QTableWidget(0, 4)
        self.flows_table.setHorizontalHeaderLabels(["Source", "Destination", "Flux", "% de Capacité"])
        # Permettre le redimensionnement
        header = self.flows_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionsMovable(True)
        
        flows_layout.addWidget(self.flows_table)
        
        flows_group.setLayout(flows_layout)
        layout.addWidget(flows_group)
        
        # Analyse de sensibilité
        sensitivity_group = QGroupBox("Analyse de Sensibilité")
        sensitivity_layout = QVBoxLayout()
        
        self.sensitivity_text = QTextEdit()
        self.sensitivity_text.setReadOnly(True)
        self.sensitivity_text.setMaximumHeight(150)
        sensitivity_layout.addWidget(self.sensitivity_text)
        
        sensitivity_group.setLayout(sensitivity_layout)
        layout.addWidget(sensitivity_group)
        
        layout.addStretch()
        
        return widget
    
    def format_number(self, value):
        """Formate un nombre avec séparateurs de milliers"""
        try:
            return f"{float(value):,.0f}"
        except:
            return str(value)
    
    def create_viz_tab(self):
        """Crée l'onglet de visualisation"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Contrôles de visualisation
        controls_layout = QHBoxLayout()
        
        self.viz_type_combo = QComboBox()
        self.viz_type_combo.addItems(["Graphe de Flux", "Diagramme à Barres", 
                                      "Carte Thermique", "Comparaison de Scénarios"])
        
        self.refresh_viz_btn = QPushButton("Actualiser la Visualisation")
        self.save_viz_btn = QPushButton("Sauvegarder l'Image")
        
        controls_layout.addWidget(QLabel("Type de visualisation:"))
        controls_layout.addWidget(self.viz_type_combo)
        controls_layout.addWidget(self.refresh_viz_btn)
        controls_layout.addWidget(self.save_viz_btn)
        controls_layout.addStretch()
        
        layout.addLayout(controls_layout)
        
        # Zone de visualisation
        self.viz_canvas = FigureCanvas(Figure(figsize=(10, 6)))
        layout.addWidget(self.viz_canvas)
        
        return widget
    
    def create_analysis_tab(self):
        """Crée l'onglet d'analyse"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Statistiques
        stats_group = QGroupBox("Statistiques du Réseau")
        stats_layout = QFormLayout()
        
        self.total_flow_label = QLabel("N/A")
        self.avg_cost_label = QLabel("N/A")
        self.capacity_usage_label = QLabel("N/A")
        self.critical_arcs_label = QLabel("N/A")
        
        stats_layout.addRow("Flux total:", self.total_flow_label)
        stats_layout.addRow("Coût moyen (%):", self.avg_cost_label)
        stats_layout.addRow("Utilisation moyenne capacité:", self.capacity_usage_label)
        stats_layout.addRow("Arcs critiques (>90%):", self.critical_arcs_label)
        
        stats_group.setLayout(stats_layout)
        layout.addWidget(stats_group)
        
        # Recommandations
        rec_group = QGroupBox("Recommandations")
        rec_layout = QVBoxLayout()
        
        self.recommendations_text = QTextEdit()
        self.recommendations_text.setReadOnly(True)
        rec_layout.addWidget(self.recommendations_text)
        
        rec_group.setLayout(rec_layout)
        layout.addWidget(rec_group)
        
        # Logs
        log_group = QGroupBox("Journal d'Optimisation")
        log_layout = QVBoxLayout()
        
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(150)
        log_layout.addWidget(self.log_text)
        
        log_group.setLayout(log_layout)
        layout.addWidget(log_group)
        
        layout.addStretch()
        
        return widget
    
    def apply_stylesheet(self):
        """Applique une feuille de style à l'application"""
        style = """
        QMainWindow {
            background-color: #f5f5f5;
        }
        QGroupBox {
            font-weight: bold;
            font-size: 11pt;
            border: 2px solid #cccccc;
            border-radius: 8px;
            margin-top: 10px;
            padding-top: 15px;
            background-color: white;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 15px;
            padding: 0 8px 0 8px;
            color: #2c3e50;
            font-weight: bold;
        }
        QTableWidget {
            background-color: white;
            alternate-background-color: #f8f9fa;
            selection-background-color: #2196F3;
            gridline-color: #dee2e6;
            font-size: 10pt;
        }
        QTableWidget::item {
            padding: 6px;
        }
        QHeaderView::section {
            background-color: #34495e;
            color: white;
            padding: 8px;
            font-weight: bold;
            font-size: 10pt;
            border: none;
        }
        QTextEdit {
            background-color: white;
            border: 1px solid #ced4da;
            border-radius: 4px;
            font-size: 10pt;
        }
        QPushButton {
            padding: 8px 16px;
            border-radius: 4px;
            font-weight: 500;
            font-size: 10pt;
        }
        QProgressBar {
            border: 1px solid #ccc;
            border-radius: 3px;
            text-align: center;
            height: 20px;
        }
        QProgressBar::chunk {
            background-color: #4CAF50;
            border-radius: 3px;
        }
        QCheckBox {
            spacing: 8px;
        }
        QComboBox {
            padding: 5px;
            border: 1px solid #ced4da;
            border-radius: 4px;
            background-color: white;
        }
        """
        self.setStyleSheet(style)
    
    def setup_connections(self):
        """Connecte les signaux et slots"""
        self.configure_btn.clicked.connect(self.configure_network)
        self.test_btn.clicked.connect(self.load_test)
        self.solve_btn.clicked.connect(self.solve_optimization)
        self.export_btn.clicked.connect(self.export_results)
        self.refresh_viz_btn.clicked.connect(self.refresh_visualization)
        self.save_viz_btn.clicked.connect(self.save_visualization)

        self.risk_checkbox.stateChanged.connect(self.update_options_display)
        self.multi_currency_checkbox.stateChanged.connect(self.update_options_display)
        self.time_constraint_checkbox.stateChanged.connect(self.update_options_display)
        
        # Connecter les signaux du thread de résolution
        self.solving_started.connect(self.on_solving_started)
        self.solving_finished.connect(self.on_solving_finished)
    
    def load_test(self):
        """Charge un fichier de test depuis le dossier data"""
        # Créer le dossier data s'il n'existe pas
        data_dir = "data"
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)
            QMessageBox.information(self, "Dossier créé", 
                                   f"Le dossier '{data_dir}' a été créé. Ajoutez-y vos fichiers JSON de test.")
            return
        
        # Lister les fichiers JSON disponibles
        test_files = [f for f in os.listdir(data_dir) if f.endswith('.json')]
        
        if not test_files:
            QMessageBox.warning(self, "Aucun test", 
                               f"Aucun fichier JSON trouvé dans le dossier '{data_dir}'")
            return
        
        # Créer un menu pour sélectionner le test
        menu = QMenu(self)
        
        for test_file in test_files:
            action = menu.addAction(test_file)
            action.setData(test_file)
        
        # Afficher le menu
        pos = self.test_btn.mapToGlobal(self.test_btn.rect().bottomLeft())
        action = menu.exec(pos)
        
        if action:
            test_file = action.data()
            self.load_test_file(os.path.join(data_dir, test_file))
    
    def load_test_file(self, file_path):
        """Charge un fichier de test spécifique"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                test_data = json.load(f)
        
            # Charger les données du réseau
            self.network_data = test_data['network_data']
            self.supply_demand = test_data['supply_demand']
        
            # ⚠️ CORRECTION ICI : Charger les options et mettre à jour les checkboxes
            options = test_data.get('options', {})
        
            # Mettre à jour les checkboxes AVANT d'afficher le message
            self.risk_checkbox.setChecked(options.get('include_risk', False))
            self.multi_currency_checkbox.setChecked(options.get('multi_currency', False))
            self.time_constraint_checkbox.setChecked(options.get('time_constraints', False))
        
            # Mettre à jour les tables
            self.update_data_tables()
        
            # Mettre à jour le statut
            test_name = test_data.get('name', os.path.basename(file_path))
            self.network_info_label.setText(f"Test chargé: {test_name} ({len(self.network_data['nodes'])} nœuds, "f"{len(self.network_data['arcs'])} arcs)"
        )
        
            # Afficher les options chargées
            options_text = "Options: "
            options_text += f"💰 Risque: {'✓' if options.get('include_risk') else '✗'}, "
            options_text += f"🌍 Multi-devises: {'✓' if options.get('multi_currency') else '✗'}, "
            options_text += f"⏱️ Temps: {'✓' if options.get('time_constraints') else '✗'}"
            self.network_info_label.setText(f"{self.network_info_label.text()} - {options_text}"
        )
        
            # Effacer les résultats précédents
            self.results = None
            self.clear_results_tab()
        
            # Log
            description = test_data.get('description', '')
            self.log_message(f"✅ Test chargé: {test_name}")
            self.log_message(f"📋 Description: {description}")
        
            # Afficher un message sur les options
            if options:
                active_options = []
                if options.get('include_risk'):
                    active_options.append("Risque de change")
                if options.get('multi_currency'):
                    active_options.append("Multi-devises")
                if options.get('time_constraints'):
                    active_options.append("Contraintes temps")
            
                if active_options:
                    self.log_message(f"⚙️ Options activées: {', '.join(active_options)}")
        
        except json.JSONDecodeError as e:
            QMessageBox.critical(self, "Erreur JSON", f"Erreur dans le fichier JSON:\n{str(e)}")
        except KeyError as e:
            QMessageBox.critical(self, "Erreur de structure", f"Clé manquante dans le test: {str(e)}")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement du test:\n{str(e)}")
    
    def reset_advanced_options(self):
        """Réinitialise les options avancées à leurs valeurs par défaut"""
        self.risk_checkbox.setChecked(False)
        self.multi_currency_checkbox.setChecked(False)
        self.time_constraint_checkbox.setChecked(False)
    
    def clear_results_tab(self):
        """Efface les résultats affichés"""
        self.objective_label.setText("N/A")
        self.solving_time_label.setText("N/A")
        self.status_label_results.setText("N/A")
        self.flows_table.setRowCount(0)
        self.sensitivity_text.clear()
        
        # Effacer l'analyse
        self.total_flow_label.setText("N/A")
        self.avg_cost_label.setText("N/A")
        self.capacity_usage_label.setText("N/A")
        self.critical_arcs_label.setText("N/A")
        self.recommendations_text.clear()
    
    
    def load_sample_data(self):
        """Charge des données d'exemple"""
        sample_nodes = ["BNP_EUR", "SG_USD", "HSBC_GBP", "Deutsche_EUR", "JPMorgan_USD"]
        sample_arcs = [
            {"source": "BNP_EUR", "destination": "SG_USD", "cost": 1.5, "capacity": 1000000},
            {"source": "SG_USD", "destination": "HSBC_GBP", "cost": 2.0, "capacity": 500000},
            {"source": "HSBC_GBP", "destination": "JPMorgan_USD", "cost": 1.0, "capacity": 750000},
            {"source": "BNP_EUR", "destination": "Deutsche_EUR", "cost": 0.5, "capacity": 1500000},
            {"source": "Deutsche_EUR", "destination": "JPMorgan_USD", "cost": 1.2, "capacity": 800000}
    ]
    
        self.network_data = {
            'nodes': sample_nodes,
            'arcs': sample_arcs
    }
    
        # Offre/demande par défaut
        self.supply_demand = {
            "BNP_EUR": 1000000,
            "SG_USD": 0,
            "HSBC_GBP": 0,
            "Deutsche_EUR": 500000,
            "JPMorgan_USD": -1500000
    }
    
        # ⚠️ CORRECTION: Réinitialiser les options
        self.reset_advanced_options()
    
        self.update_data_tables()
        self.network_info_label.setText(f"Réseau: {len(sample_nodes)} nœuds, {len(sample_arcs)} arcs")
        self.update_options_display()  # Mettre à jour l'affichage
    
        self.log_message("✅ Données d'exemple chargées")
        self.log_message("⚙️ Options avancées réinitialisées")
    
    def configure_network(self):
        """Ouvre le dialogue de configuration du réseau"""
        dialog = NetworkInputDialog(self)
        if dialog.exec():
            network_data = dialog.get_network_data()
            self.network_data = network_data
        
            # ⚠️ CORRECTION: Réinitialiser l'offre/demande et les options
            self.supply_demand = {node: 0 for node in network_data['nodes']}
        
            # Réinitialiser les options avancées
            self.reset_advanced_options()
        
            # Mettre à jour les tables
            self.update_data_tables()
        
            self.network_info_label.setText(f"Réseau configuré: {len(network_data['nodes'])} nœuds, "f"{len(network_data['arcs'])} arcs"
        )
        
            self.log_message("✅ Réseau configuré avec succès")
            self.log_message("⚙️ Options avancées réinitialisées")
    
    def update_options_display(self):
        """Met à jour l'affichage visuel des options"""
        options_text = "Options: "
        options_text += f"💰 Risque: {'✓' if self.risk_checkbox.isChecked() else '✗'}, "
        options_text += f"🌍 Multi-devises: {'✓' if self.multi_currency_checkbox.isChecked() else '✗'}, "
        options_text += f"⏱️ Temps: {'✓' if self.time_constraint_checkbox.isChecked() else '✗'}"
    
        # Mettre à jour le label d'info réseau
        current_text = self.network_info_label.text()
        # Supprimer l'ancienne info options si présente
        if " - Options:" in current_text:
            current_text = current_text.split(" - Options:")[0]
    
        # Ajouter la nouvelle info
        self.network_info_label.setText(f"{current_text} - {options_text}")
    
    def update_data_tables(self):
        """Met à jour les tables de données avec les devises"""
        if not self.network_data:
            return
    
        # ============================================
        # TABLE DES NŒUDS (avec colonne Devise)
        # ============================================
        self.nodes_table.setRowCount(len(self.network_data['nodes']))
    
        # Définir les en-têtes avec colonne Devise
        self.nodes_table.setColumnCount(4)  # +1 pour la devise
        self.nodes_table.setHorizontalHeaderLabels([
            "Banque/Compte", 
            "Devise",  # NOUVELLE COLONNE
            "Type", 
            "Valeur"
    ])
    
        for i, node in enumerate(self.network_data['nodes']):
            # Colonne 0: Nom du nœud
            self.nodes_table.setItem(i, 0, QTableWidgetItem(node))
        
            # Colonne 1: Devise (extraite du nom)
            if '_' in node:
                currency = node.split('_')[-1]
                currency_item = QTableWidgetItem(currency)
                # Colorer selon la devise
                currency_colors = {
                    'EUR': QColor(0, 123, 255),    # Bleu
                    'USD': QColor(40, 167, 69),    # Vert
                    'GBP': QColor(220, 53, 69),    # Rouge
                    'CHF': QColor(255, 193, 7),    # Jaune
                    'JPY': QColor(111, 66, 193)    # Violet
            }
                if currency in currency_colors:
                    currency_item.setForeground(currency_colors[currency])
                self.nodes_table.setItem(i, 1, currency_item)
            else:
                self.nodes_table.setItem(i, 1, QTableWidgetItem("N/A"))
        
            # Colonne 2: Type (offre/demande)
            type_combo = QComboBox()
            type_combo.addItems(["Neutre", "Offre (+)", "Demande (-)"])
            if node in self.supply_demand:
                if self.supply_demand[node] > 0:
                    type_combo.setCurrentIndex(1)
                elif self.supply_demand[node] < 0:
                    type_combo.setCurrentIndex(2)
        
            # Connecter le changement de type
            type_combo.currentIndexChanged.connect(
                lambda idx, n=node: self.update_node_type(n, idx)
        )
            self.nodes_table.setCellWidget(i, 2, type_combo)
        
            # Colonne 3: Valeur
            value = abs(self.supply_demand.get(node, 0))
            value_item = QTableWidgetItem(f"{value:,.0f}")
            self.nodes_table.setItem(i, 3, value_item)
    
        # Configurer l'en-tête pour permettre le redimensionnement manuel
        header = self.nodes_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionsMovable(True)
        
        # Ajuster la largeur des colonnes
        if self.nodes_table.rowCount() > 0:
            self.nodes_table.resizeColumnsToContents()
            # Ajuster les largeurs minimales
            self.nodes_table.setColumnWidth(0, max(200, self.nodes_table.columnWidth(0)))
            self.nodes_table.setColumnWidth(1, max(80, self.nodes_table.columnWidth(1)))
            self.nodes_table.setColumnWidth(2, max(100, self.nodes_table.columnWidth(2)))
            self.nodes_table.setColumnWidth(3, max(120, self.nodes_table.columnWidth(3)))
    
        # ============================================
        # TABLE DES ARCS (avec colonnes Devises)
        # ============================================
        self.arcs_table.setRowCount(len(self.network_data['arcs']))
    
        # Définir les en-têtes avec colonnes Devises
        self.arcs_table.setColumnCount(7)  # +2 pour les devises source/dest
        self.arcs_table.setHorizontalHeaderLabels([
            "Source", 
            "Dev. Source",  # NOUVELLE
            "Destination", 
            "Dev. Dest",    # NOUVELLE
            "Coût (%)", 
            "Capacité Max", 
            "Actif"
    ])
    
        for i, arc in enumerate(self.network_data['arcs']):
            source = arc['source']
            dest = arc['destination']
        
            # Colonne 0: Source
            self.arcs_table.setItem(i, 0, QTableWidgetItem(source))
        
            # Colonne 1: Devise Source
            if '_' in source:
                src_currency = source.split('_')[-1]
                src_currency_item = QTableWidgetItem(src_currency)
                # Même colorisation que pour les nœuds
                currency_colors = {
                    'EUR': QColor(0, 123, 255),
                    'USD': QColor(40, 167, 69),
                    'GBP': QColor(220, 53, 69),
                    'CHF': QColor(255, 193, 7),
                    'JPY': QColor(111, 66, 193)
            }
                if src_currency in currency_colors:
                    src_currency_item.setForeground(currency_colors[src_currency])
                self.arcs_table.setItem(i, 1, src_currency_item)
            else:
                self.arcs_table.setItem(i, 1, QTableWidgetItem("N/A"))
        
            # Colonne 2: Destination
            self.arcs_table.setItem(i, 2, QTableWidgetItem(dest))
        
            # Colonne 3: Devise Destination
            if '_' in dest:
                dest_currency = dest.split('_')[-1]
                dest_currency_item = QTableWidgetItem(dest_currency)
                if dest_currency in currency_colors:
                    dest_currency_item.setForeground(currency_colors[dest_currency])
                self.arcs_table.setItem(i, 3, dest_currency_item)
            
                # Surligner si changement de devise
                if '_' in source and source.split('_')[-1] != dest_currency:
                    self.arcs_table.item(i, 0).setBackground(QColor(255, 248, 225))  # Jaune clair
                    self.arcs_table.item(i, 2).setBackground(QColor(255, 248, 225))
            else:
                self.arcs_table.setItem(i, 3, QTableWidgetItem("N/A"))
        
            # Colonne 4: Coût
            cost_item = QTableWidgetItem(f"{arc['cost']:.3f}")
            self.arcs_table.setItem(i, 4, cost_item)
        
            # Colonne 5: Capacité
            capacity_item = QTableWidgetItem(f"{arc['capacity']:,.0f}")
            self.arcs_table.setItem(i, 5, capacity_item)
        
            # Colonne 6: Case à cocher pour activer/désactiver l'arc
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            self.arcs_table.setCellWidget(i, 6, checkbox)
    
        # Configurer l'en-tête pour permettre le redimensionnement manuel
        header = self.arcs_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionsMovable(True)
        
        # Ajuster la largeur des colonnes
        if self.arcs_table.rowCount() > 0:
            self.arcs_table.resizeColumnsToContents()
            # Ajuster les largeurs minimales
            self.arcs_table.setColumnWidth(0, max(150, self.arcs_table.columnWidth(0)))
            self.arcs_table.setColumnWidth(1, max(80, self.arcs_table.columnWidth(1)))
            self.arcs_table.setColumnWidth(2, max(150, self.arcs_table.columnWidth(2)))
            self.arcs_table.setColumnWidth(3, max(80, self.arcs_table.columnWidth(3)))
            self.arcs_table.setColumnWidth(4, max(80, self.arcs_table.columnWidth(4)))
            self.arcs_table.setColumnWidth(5, max(120, self.arcs_table.columnWidth(5)))
            self.arcs_table.setColumnWidth(6, max(60, self.arcs_table.columnWidth(6)))
    
        # ============================================
        # AJOUTER UN RÉSUMÉ DES DEVISES
        # ============================================
        self.update_currency_summary()

    def update_currency_summary(self):
        """Affiche un résumé des devises détectées"""
        if not self.network_data:
            return
    
        currencies = {}
        for node in self.network_data['nodes']:
            if '_' in node:
                currency = node.split('_')[-1]
                currencies[currency] = currencies.get(currency, 0) + 1
    
        if currencies:
            summary_text = f"Devises détectées: {len(currencies)} ("
            summary_text += ", ".join([f"{c}: {n}" for c, n in sorted(currencies.items())])
            summary_text += ")"
        
            # Créer ou mettre à jour le label de résumé
            if not hasattr(self, 'currency_summary_label'):
                self.currency_summary_label = QLabel()
                # Insérer après le groupe d'info réseau
                layout = self.data_tab.layout()
                if layout:
                    layout.insertWidget(1, self.currency_summary_label)
        
            self.currency_summary_label.setText(summary_text)
        
            # Log pour information
            if len(currencies) > 1:
                self.log_message(f"🌍 {len(currencies)} devises détectées: {', '.join(currencies.keys())}")
            else:
                self.log_message(f"💰 1 devise détectée: {list(currencies.keys())[0]}")
    
    def update_node_type(self, node, type_idx):
        """Met à jour le type d'un nœud (offre/demande)"""
        # Récupérer la valeur de la table
        for i in range(self.nodes_table.rowCount()):
            if self.nodes_table.item(i, 0).text() == node:
                value_text = self.nodes_table.item(i, 2).text()
                try:
                    value = float(value_text)
                except ValueError:
                    value = 0
                
                # Mettre à jour le dictionnaire
                if type_idx == 1:  # Offre
                    self.supply_demand[node] = value
                elif type_idx == 2:  # Demande
                    self.supply_demand[node] = -value
                else:  # Neutre
                    self.supply_demand[node] = 0
                break
    
    def solve_optimization(self):
        """Lance la résolution du problème d'optimisation"""
        if not self.network_data:
            QMessageBox.warning(self, "Données manquantes", 
                               "Veuillez configurer un réseau d'abord.")
            return
        
        # Récupérer les données actuelles des tables
        self.collect_data_from_tables()
        
        # Options avancées
        options = {
            'include_risk': self.risk_checkbox.isChecked(),
            'multi_currency': self.multi_currency_checkbox.isChecked(),
            'time_constraints': self.time_constraint_checkbox.isChecked()
        }
        
        # Créer et lancer le thread de résolution
        self.solver_thread = GurobiThread(self.network_data, self.supply_demand, options)
        self.solver_thread.solution_ready.connect(self.on_solution_ready)
        self.solver_thread.error_occurred.connect(self.on_solver_error)
        
        self.solver_thread.start()
        self.solving_started.emit()
    
    def collect_data_from_tables(self):
        """Collecte les données des tables (avec nouvelle structure)"""
        # Collecter l'offre/demande
        for i in range(self.nodes_table.rowCount()):
            node = self.nodes_table.item(i, 0).text()
            value_text = self.nodes_table.item(i, 3).text().replace(',', '')
        
            try:
                value = float(value_text)
            except ValueError:
                value = 0
        
            type_combo = self.nodes_table.cellWidget(i, 2)
            if type_combo.currentIndex() == 1:  # Offre
                self.supply_demand[node] = value
            elif type_combo.currentIndex() == 2:  # Demande
                self.supply_demand[node] = -value
            else:
                self.supply_demand[node] = 0
    
        # Collecter les arcs actifs (avec nouvelle structure à 7 colonnes)
        active_arcs = []
        for i in range(self.arcs_table.rowCount()):
            checkbox = self.arcs_table.cellWidget(i, 6)
            if checkbox.isChecked():
                arc = {
                    'source': self.arcs_table.item(i, 0).text(),
                    'destination': self.arcs_table.item(i, 2).text(),
                    'cost': float(self.arcs_table.item(i, 4).text()),
                    'capacity': float(self.arcs_table.item(i, 5).text().replace(',', ''))
            }
                active_arcs.append(arc)
    
        self.network_data['arcs'] = active_arcs

    def on_solution_ready(self, results):
        """Traite la solution reçue du solveur"""
        print("=== DÉBOGAGE Résultats reçus ===")
        print("Clés disponibles:", results.keys())
    
        # Vérifier et garantir que 'objective' est un nombre valide
        if 'objective' in results:
            obj_value = results['objective']
            print(f"Valeur brute de 'objective': {obj_value}")
            print(f"Type de 'objective': {type(obj_value)}")
        
            # Si None, mettre à 0
            if obj_value is None:
                results['objective'] = 0.0
                print("Objective était None, corrigé à 0.0")
            # S'assurer que c'est un nombre
            elif not isinstance(obj_value, (int, float)):
                try:
                    results['objective'] = float(obj_value)
                    print(f"Objective converti en float: {results['objective']}")
                except (ValueError, TypeError):
                    results['objective'] = 0.0
                    print("Erreur de conversion, objective mis à 0.0")
        else:
            print("ATTENTION: 'objective' non trouvé dans les résultats")
            results['objective'] = 0.0
    
        print("Statut:", results.get('status'))
        print("Flux disponibles:", bool(results.get('flows')))
    
        self.results = results
        self.update_results_tab()
    
        # Rafraîchir la visualisation seulement si des flux existent
        if results.get('flows'):
            self.refresh_visualization()
    
        self.update_analysis_tab()
    
        self.solving_finished.emit()
        self.log_message("✅ Optimisation terminée avec succès")
    
    def on_solver_error(self, error_msg):
        """Traite les erreurs du solveur"""
        QMessageBox.critical(self, "Erreur du Solveur", error_msg)
        self.solving_finished.emit()
        self.log_message(f"❌ Erreur: {error_msg}")
    
    def on_solving_started(self):
        """Démarre l'interface pendant la résolution"""
        self.solve_btn.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Mode indeterminé
        self.status_label.setText("Résolution en cours...")
    
    def on_solving_finished(self):
        """Remet l'interface après la résolution"""
        self.solve_btn.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Prêt")
    
    # Dans la classe MainWindow, modifiez update_results_tab():

    def update_results_tab(self):
        """Met à jour l'onglet des résultats avec les devises"""
        if not self.results:
            return
        
        # ============================================
        # RÉSUMÉ DES RÉSULTATS
        # ============================================
        objective_value = self.results.get('objective')
        if objective_value is not None:
            try:
                objective_value = float(objective_value)
                self.objective_label.setText(f"{objective_value:,.2f} €")
            except (ValueError, TypeError):
                self.objective_label.setText("N/A")
        else:
            self.objective_label.setText("N/A")
        
        self.solving_time_label.setText(f"{self.results.get('solving_time', 0):.2f} secondes")
        self.status_label_results.setText(self.results.get('status', 'N/A'))
        
        # ============================================
        # AFFICHER LES OPTIONS APPLIQUÉES
        # ============================================
        options = self.results.get('options_applied', {})
        if options:
            options_text = "🔧 Options appliquées: "
            options_text += f"💰 Risque: {'✅' if options.get('include_risk') else '❌'}, "
            options_text += f"🌍 Multi-devises: {'✅' if options.get('multi_currency') else '❌'}, "
            options_text += f"⏱️ Temps: {'✅' if options.get('time_constraints') else '❌'}"
            
            # Créer ou mettre à jour le label d'options
            if not hasattr(self, 'options_applied_label'):
                self.options_applied_label = QLabel()
                self.options_applied_label.setStyleSheet("""
                    QLabel {
                        color: #2c3e50;
                        font-weight: bold;
                        padding: 5px;
                        background-color: #e9ecef;
                        border-radius: 4px;
                        border: 1px solid #ced4da;
                    }
                """)
                # Trouver le layout du groupe de résumé et insérer après
                summary_group = self.results_tab.findChild(QGroupBox)
                if summary_group:
                    summary_layout = summary_group.layout()
                    if isinstance(summary_layout, QFormLayout):
                        summary_layout.addRow("Options:", self.options_applied_label)
            
            self.options_applied_label.setText(options_text)
            
            # Afficher le nombre d'arcs modifiés si disponible
            arcs_modified = self.results.get('arcs_modified', 0)
            if arcs_modified > 0:
                modification_text = f"📊 {arcs_modified} arcs modifiés par les options"
                if not hasattr(self, 'modification_label'):
                    self.modification_label = QLabel()
                    self.modification_label.setStyleSheet("""
                        QLabel {
                            color: #0c5460;
                            font-weight: bold;
                            padding: 5px;
                            background-color: #d1ecf1;
                            border-radius: 4px;
                            border: 1px solid #bee5eb;
                        }
                    """)
                    summary_layout.addRow("Modifications:", self.modification_label)
                self.modification_label.setText(modification_text)
        
        # ============================================
        # TABLE DES FLUX OPTIMAUX (avec colonnes de devises)
        # ============================================
        flows = self.results.get('flows', {})
        
        # Configurer la table des flux (6 colonnes maintenant)
        self.flows_table.setColumnCount(6)
        self.flows_table.setHorizontalHeaderLabels([
            "Source", 
            "Devise Source",  # NOUVELLE
            "Destination", 
            "Devise Dest",    # NOUVELLE
            "Flux (€)", 
            "% Capacité"
        ])
        
        # Configuration de l'en-tête - Permettre le redimensionnement
        header = self.flows_table.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSectionsMovable(True)
        
        self.flows_table.setRowCount(len(flows))
        
        # Dictionnaire de couleurs pour les devises
        currency_colors = {
            'EUR': QColor(0, 123, 255),    # Bleu
            'USD': QColor(40, 167, 69),    # Vert
            'GBP': QColor(220, 53, 69),    # Rouge
            'CHF': QColor(255, 193, 7),    # Jaune
            'JPY': QColor(111, 66, 193)    # Violet
        }
        
        total_flow = 0
        inter_currency_transfers = 0
        
        for i, ((source, dest), flow) in enumerate(flows.items()):
            total_flow += flow
            
            # ========================================
            # COLONNE 0: Source
            # ========================================
            source_item = QTableWidgetItem(source)
            self.flows_table.setItem(i, 0, source_item)
            
            # ========================================
            # COLONNE 1: Devise Source
            # ========================================
            src_currency = ""
            if '_' in source:
                src_currency = source.split('_')[-1]
                src_currency_item = QTableWidgetItem(src_currency)
                
                # Colorer selon la devise
                if src_currency in currency_colors:
                    src_currency_item.setForeground(currency_colors[src_currency])
                    src_currency_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                
                self.flows_table.setItem(i, 1, src_currency_item)
            else:
                self.flows_table.setItem(i, 1, QTableWidgetItem(""))
            
            # ========================================
            # COLONNE 2: Destination
            # ========================================
            dest_item = QTableWidgetItem(dest)
            self.flows_table.setItem(i, 2, dest_item)
            
            # ========================================
            # COLONNE 3: Devise Destination
            # ========================================
            dest_currency = ""
            if '_' in dest:
                dest_currency = dest.split('_')[-1]
                dest_currency_item = QTableWidgetItem(dest_currency)
                
                # Colorer selon la devise
                if dest_currency in currency_colors:
                    dest_currency_item.setForeground(currency_colors[dest_currency])
                    dest_currency_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                
                self.flows_table.setItem(i, 3, dest_currency_item)
            else:
                self.flows_table.setItem(i, 3, QTableWidgetItem(""))
            
            # ========================================
            # COLONNE 4: Flux
            # ========================================
            flow_item = QTableWidgetItem(f"{flow:,.2f}")
            flow_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            
            # Colorer les flux importants
            if flow > 1000000:  # Plus d'1 million
                flow_item.setForeground(QColor(220, 53, 69))  # Rouge
                flow_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            elif flow > 500000:  # Plus de 500k
                flow_item.setForeground(QColor(255, 193, 7))   # Jaune
            
            self.flows_table.setItem(i, 4, flow_item)
            
            # ========================================
            # COLONNE 5: % de Capacité
            # ========================================
            capacity = 1
            for arc in self.network_data['arcs']:
                if arc['source'] == source and arc['destination'] == dest:
                    capacity = arc['capacity']
                    break
            
            if capacity > 0:
                usage_percent = (flow / capacity) * 100
                usage_item = QTableWidgetItem(f"{usage_percent:.1f}%")
                usage_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                
                # Colorer en fonction de l'utilisation
                if usage_percent > 90:
                    usage_item.setForeground(QColor(220, 53, 69))  # Rouge
                    usage_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                elif usage_percent > 70:
                    usage_item.setForeground(QColor(255, 193, 7))   # Jaune
                    usage_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
                
                self.flows_table.setItem(i, 5, usage_item)
                
                # Surligner les transferts inter-devises
                if src_currency and dest_currency and src_currency != dest_currency:
                    inter_currency_transfers += 1
                    # Colorer la ligne en jaune clair pour les transferts inter-devises
                    for col in range(6):
                        item = self.flows_table.item(i, col)
                        if item:
                            item.setBackground(QColor(255, 248, 225))  # Jaune très clair
        
        # Ajuster la largeur des colonnes
        if self.flows_table.rowCount() > 0:
            self.flows_table.resizeColumnsToContents()
            # Largeurs minimales
            self.flows_table.setColumnWidth(0, max(150, self.flows_table.columnWidth(0)))
            self.flows_table.setColumnWidth(1, max(80, self.flows_table.columnWidth(1)))
            self.flows_table.setColumnWidth(2, max(150, self.flows_table.columnWidth(2)))
            self.flows_table.setColumnWidth(3, max(80, self.flows_table.columnWidth(3)))
            self.flows_table.setColumnWidth(4, max(120, self.flows_table.columnWidth(4)))
            self.flows_table.setColumnWidth(5, max(100, self.flows_table.columnWidth(5)))
        
        # ============================================
        # ANALYSE DE SENSIBILITÉ AVEC INFO DEVISE
        # ============================================
        sensitivity_text = ""
        
        # Ajouter info sur l'impact des options
        if 'options_applied' in self.results and self.results.get('arcs_modified', 0) > 0:
            sensitivity_text += "🔧 IMPACT DES OPTIONS:\n"
            sensitivity_text += f"  • {self.results['arcs_modified']} arcs modifiés\n"
            
            # Calculer l'impact approximatif
            if 'original_costs' in self.results and 'modified_costs' in self.results:
                total_impact = 0
                for (source, dest), flow in flows.items():
                    arc_key = f"{source}→{dest}"
                    if arc_key in self.results['original_costs'] and arc_key in self.results['modified_costs']:
                        orig = self.results['original_costs'][arc_key]
                        mod = self.results['modified_costs'][arc_key]
                        impact = (mod - orig) * flow
                        total_impact += impact
                
                if abs(total_impact) > 0.01:
                    impact_text = "🔺 Augmentation" if total_impact > 0 else "🔻 Réduction"
                    sensitivity_text += f"  • {impact_text} de coût: {abs(total_impact):+,.0f} €\n"
        
        # Info sur les transferts inter-devises
        if inter_currency_transfers > 0:
            sensitivity_text += f"\n🌍 TRANSFERTS INTER-DEVISES:\n"
            sensitivity_text += f"  • {inter_currency_transfers} transferts sur {len(flows)} total\n"
            
            # Calculer le pourcentage
            if len(flows) > 0:
                percent_inter = (inter_currency_transfers / len(flows)) * 100
                sensitivity_text += f"  • {percent_inter:.1f}% des transferts\n"
        
        # Info sur le flux total
        if total_flow > 0:
            sensitivity_text += f"\n📊 SYNTHÈSE DU FLUX:\n"
            sensitivity_text += f"  • Flux total: {total_flow:,.0f} €\n"
            sensitivity_text += f"  • Nombre d'arcs actifs: {len(flows)}\n"
            
            if objective_value and objective_value > 0:
                avg_cost = objective_value / total_flow
                sensitivity_text += f"  • Coût moyen: {avg_cost:.4f} €/€\n"
        
        # Coûts réduits
        if 'reduced_costs' in self.results:
            rc_dict = self.results['reduced_costs']
            if rc_dict:
                sensitivity_text += "\n📉 COÛTS RÉDUITS (analyse marginale):\n"
                count = 0
                for (i, j), rc in rc_dict.items():
                    if abs(rc) > 0.001:
                        # Extraire les devises si disponibles
                        src_curr = i.split('_')[-1] if '_' in i else "?"
                        dest_curr = j.split('_')[-1] if '_' in j else "?"
                        
                        sensitivity_text += f"  • {i}→{j}: {rc:.4f} "
                        if src_curr != dest_curr:
                            sensitivity_text += f"[{src_curr}→{dest_curr}]\n"
                        else:
                            sensitivity_text += f"[même devise]\n"
                        count += 1
                        if count >= 5:  # Limiter à 5 pour éviter trop d'info
                            sensitivity_text += f"  • ... et {len(rc_dict) - count} autres\n"
                            break
        
        # Prix duaux
        if 'shadow_prices' in self.results:
            sp_dict = self.results['shadow_prices']
            if sp_dict:
                sensitivity_text += "\n💰 PRIX DUAUX (valeur marginale):\n"
                for node, sp in list(sp_dict.items())[:5]:  # Limiter à 5
                    sensitivity_text += f"  • {node}: {sp:.4f}\n"
                if len(sp_dict) > 5:
                    sensitivity_text += f"  • ... et {len(sp_dict) - 5} autres nœuds\n"
        
        self.sensitivity_text.setText(sensitivity_text)
        
        # ============================================
        # MISE À JOUR DES STATISTIQUES (optionnel)
        # ============================================
        try:
            # Ces labels doivent exister dans l'onglet Analyse
            if hasattr(self, 'total_flow_label'):
                self.total_flow_label.setText(f"{total_flow:,.2f} €")
            
            if hasattr(self, 'inter_currency_label'):
                self.inter_currency_label.setText(f"{inter_currency_transfers} transferts")
            
            if total_flow > 0 and objective_value and objective_value > 0:
                avg_cost = objective_value / total_flow
                if hasattr(self, 'avg_cost_label'):
                    self.avg_cost_label.setText(f"{avg_cost:.4f} €/€")
        except:
            pass
        
        # ============================================
        # AJOUTER UN RÉSUMÉ VISUEL EN HAUT DE LA TABLE
        # ============================================
        if len(flows) > 0:
            summary_info = f"📈 {len(flows)} flux optimaux | Total: {total_flow:,.0f} €"
            if inter_currency_transfers > 0:
                summary_info += f" | 🌍 {inter_currency_transfers} transferts inter-devises"
            
            # Créer ou mettre à jour un label de résumé
            if not hasattr(self, 'flows_summary_label'):
                self.flows_summary_label = QLabel()
                self.flows_summary_label.setStyleSheet("""
                    QLabel {
                        color: #155724;
                        font-weight: bold;
                        padding: 8px;
                        background-color: #d4edda;
                        border-radius: 4px;
                        border: 1px solid #c3e6cb;
                        margin-bottom: 5px;
                    }
                """)
                # Insérer avant la table des flux
                flows_group = self.results_tab.findChild(QGroupBox, "Flux Optimaux de Transfert")
                if flows_group:
                    flows_layout = flows_group.layout()
                    if flows_layout:
                        flows_layout.insertWidget(0, self.flows_summary_label)
            
            self.flows_summary_label.setText(summary_info)
    
    def refresh_visualization(self):
        """Rafraîchit la visualisation"""
        if not self.results:
            # Afficher un message si pas de résultats
            self.viz_canvas.figure.clear()
            ax = self.viz_canvas.figure.add_subplot(111)
            ax.text(0.5, 0.5, "Aucun résultat disponible\nRésolvez d'abord le problème d'optimisation", ha='center', va='center', transform=ax.transAxes, fontsize=12, bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            ax.axis('off')
            self.viz_canvas.draw()
            return
    
        if 'flows' not in self.results:
            # Afficher un message si pas de flux
            self.viz_canvas.figure.clear()
            ax = self.viz_canvas.figure.add_subplot(111)
            ax.text(0.5, 0.5, "Aucun flux disponible dans les résultats", ha='center', va='center', transform=ax.transAxes, fontsize=12,bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
            ax.axis('off')
            self.viz_canvas.draw()
            return
    
        viz_type = self.viz_type_combo.currentText()
    
        # Effacer la figure précédente
        self.viz_canvas.figure.clear()
    
        try:
            if viz_type == "Graphe de Flux":
                self.plot_network_graph()
            elif viz_type == "Diagramme à Barres":
                self.plot_bar_chart()
            elif viz_type == "Carte Thermique":
                self.plot_heatmap()
            else:  # "Comparaison de Scénarios"
                self.plot_scenario_comparison()
        
            self.viz_canvas.draw()
        except Exception as e:
            # En cas d'erreur, afficher un message
            self.viz_canvas.figure.clear()
            ax = self.viz_canvas.figure.add_subplot(111)
            error_msg = f"Erreur lors de la génération du graphique:\n{str(e)}"
            ax.text(0.5, 0.5, error_msg,ha='center', va='center', transform=ax.transAxes, fontsize=10,bbox=dict(boxstyle='round', facecolor='lightcoral', alpha=0.7))
            ax.axis('off')
            self.viz_canvas.draw()
            print(f"Erreur visualisation: {e}")
    
    def plot_network_graph(self):
        """Trace le graphe du réseau avec les flux"""
        ax = self.viz_canvas.figure.add_subplot(111)
    
        flows = self.results.get('flows', {})
    
        if not flows:
            ax.text(0.5, 0.5, "Aucun flux disponible", ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title("Graphe de Flux - Aucun Donnée")
            ax.axis('off')
            return
    
        # Créer un graphe dirigé
        G = nx.DiGraph()
    
        # Ajouter les nœuds
        for node in self.network_data['nodes']:
            G.add_node(node)
    
        # Ajouter les arcs avec les flux
        edge_labels = {}
        for (source, dest), flow in flows.items():
            if flow > 0:
                G.add_edge(source, dest, weight=flow)
                edge_labels[(source, dest)] = f"{flow:,.0f}"
    
        if len(G.edges()) == 0:
            ax.text(0.5, 0.5, "Aucun arc avec flux positif", ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title("Graphe de Flux - Aucun Arc Actif")
            ax.axis('off')
            return
    
        # Positionnement des nœuds
        try:
            pos = nx.spring_layout(G, k=2, iterations=50)
        except:
            # Fallback si le layout échoue
            pos = nx.circular_layout(G)
    
        # Tracer les nœuds
        nx.draw_networkx_nodes(G, pos, node_color='lightblue', node_size=1500, alpha=0.8, ax=ax)
    
        # Tracer les étiquettes des nœuds
        nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold', ax=ax)
    
        # Tracer les arêtes avec épaisseur proportionnelle au flux
        edges = list(G.edges(data=True))
        if edges:
            max_flow = max([d.get('weight', 0) for (u, v, d) in edges])
            if max_flow > 0:
                widths = [d.get('weight', 0) / max_flow * 5 for (u, v, d) in edges]
            else:
                widths = [2] * len(edges)  # Largeur par défaut
        
            nx.draw_networkx_edges(G, pos, edgelist=edges, width=widths, edge_color='#2196F3',arrows=True, arrowsize=20, ax=ax)
    
        # Ajouter les labels des arêtes
        if edge_labels:
            nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color='red', font_size=8, ax=ax)
    
        ax.set_title(f"Graphe des Flux de Transfert ({len(flows)} arcs)")
        ax.axis('off')

    def plot_bar_chart(self):
        """Trace un diagramme à barres des flux"""
        ax = self.viz_canvas.figure.add_subplot(111)
    
        flows = self.results.get('flows', {})
    
        if not flows:
            ax.text(0.5, 0.5, "Aucun flux disponible", ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title("Diagramme à Barres - Aucun Donnée")
            ax.axis('off')
            return
    
        arcs = list(flows.keys())
        flow_values = list(flows.values())
    
        if not flow_values:
            ax.text(0.5, 0.5, "Aucun flux disponible", ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title("Diagramme à Barres - Aucun Donnée")
            ax.axis('off')
            return
    
        # Raccourcir les labels
        arc_labels = [f"{s}→{d}" for (s, d) in arcs]
    
        bars = ax.bar(range(len(flow_values)), flow_values, color='#2196F3', alpha=0.7)
    
        # Ajouter les valeurs sur les barres
        for bar, flow in zip(bars, flow_values):
            height = bar.get_height()
            if height > 0:  # Seulement si le flux est positif
                ax.text(bar.get_x() + bar.get_width()/2., height,f'{flow:,.0f}', ha='center', va='bottom', rotation=0, fontsize=9)
    
        ax.set_xlabel('Arcs de Transfert')
        ax.set_ylabel('Montant (€)')
        ax.set_title(f'Flux Optimaux par Arc ({len(flows)} arcs)')
        ax.set_xticks(range(len(flow_values)))
        ax.set_xticklabels(arc_labels, rotation=45, ha='right')
        ax.grid(True, alpha=0.3, axis='y')
    
        # Ajuster les marges pour les labels
        plt.tight_layout()

    
    def plot_heatmap(self):
        """Trace une carte thermique des flux entre banques"""
        ax = self.viz_canvas.figure.add_subplot(111)
    
        flows = self.results.get('flows', {})
    
        if not flows:
            ax.text(0.5, 0.5, "Aucun flux disponible", ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title("Carte Thermique - Aucun Donnée")
            ax.axis('off')
            return
    
        nodes = self.network_data['nodes']
        n = len(nodes)
        flow_matrix = np.zeros((n, n))
    
        # Créer un dictionnaire d'index pour les nœuds
        node_index = {node: i for i, node in enumerate(nodes)}
    
        # Remplir la matrice
        for (source, dest), flow in flows.items():
            if source in node_index and dest in node_index:
                i = node_index[source]
                j = node_index[dest]
                flow_matrix[i, j] = flow
    
        # Vérifier s'il y a des flux
        if np.sum(flow_matrix) == 0:
            ax.text(0.5, 0.5, "Aucun flux disponible", ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title("Carte Thermique - Aucun Donnée")
            ax.axis('off')
            return
    
        im = ax.imshow(flow_matrix, cmap='YlOrRd', aspect='auto')
    
        # Ajouter les annotations seulement pour les flux > 0
        for i in range(n):
            for j in range(n):
                if flow_matrix[i, j] > 0:
                    ax.text(j, i, f'{flow_matrix[i, j]:,.0f}',ha='center', va='center', color='black', fontsize=8)
    
        ax.set_xticks(range(n))
        ax.set_yticks(range(n))
        ax.set_xticklabels(nodes, rotation=45, ha='right')
        ax.set_yticklabels(nodes)
        ax.set_xlabel('Destination', fontweight='bold')
        ax.set_ylabel('Source', fontweight='bold')
        ax.set_title('Carte Thermique des Flux Interbancaires')
    
        # Barre de couleur
        cbar = self.viz_canvas.figure.colorbar(im, ax=ax)
        cbar.set_label('Montant (€)', fontweight='bold')
    
        # Ajuster les marges
        plt.tight_layout()
    
    def plot_scenario_comparison(self):
        """Trace une comparaison de différents scénarios"""
        ax = self.viz_canvas.figure.add_subplot(111)
    
        # Récupérer la valeur objective avec vérification
        base_cost = self.results.get('objective', 0)
        if base_cost is None:
            base_cost = 0
    
        # S'assurer que base_cost est un nombre valide
        try:
            base_cost = float(base_cost)
        except (ValueError, TypeError):
            base_cost = 0
    
        # Si le coût est 0, montrer un message
        if base_cost == 0:
            ax.text(0.5, 0.5, "Coût optimal non disponible\nRésolvez d'abord le problème", ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title("Comparaison - Données Manquantes")
            ax.axis('off')
            return
    
        # Scénarios fictifs pour la démonstration
        scenarios = ['Optimisé', 'Direct', 'Via Hub', 'Sans Contraintes']
    
        # Générer des coûts pour les autres scénarios
        costs = [
            base_cost,
            base_cost * 1.3,    # 30% plus cher
            base_cost * 1.15,   # 15% plus cher
            max(0, base_cost * 0.8)     # 20% moins cher (sans contraintes), minimum 0
    ]
    
        colors = ['#4CAF50', '#FF9800', '#2196F3', '#9C27B0']
    
        bars = ax.bar(scenarios, costs, color=colors, alpha=0.7)
    
        # Ajouter les valeurs sur les barres
        for bar, cost in zip(bars, costs):
            height = bar.get_height()
            if height > 0:  # Seulement si le coût est positif
                ax.text(bar.get_x() + bar.get_width()/2., height,f'{cost:,.0f} €', ha='center', va='bottom', fontweight='bold')
    
        ax.set_ylabel('Coût Total (€)', fontweight='bold')
        ax.set_title(f'Comparaison des Stratégies de Transfert\n(Coût optimal: {base_cost:,.0f} €)', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
    
        # Ajuster la rotation des labels
        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
    
        # Ajuster les marges
        plt.tight_layout()
    
    def update_analysis_tab(self):
        """Met à jour l'onglet d'analyse"""
        if not self.results:
            return
        
        # Calculer les statistiques
        total_flow = sum(self.results['flows'].values())
        avg_cost = self.results['objective'] / total_flow if total_flow > 0 else 0
        
        # Taux d'utilisation des capacités
        usage_rates = []
        for (source, dest), flow in self.results['flows'].items():
            for arc in self.network_data['arcs']:
                if arc['source'] == source and arc['destination'] == dest:
                    if arc['capacity'] > 0:
                        usage_rates.append(flow / arc['capacity'])
                    break
        
        avg_usage = np.mean(usage_rates) * 100 if usage_rates else 0
        
        # Arcs critiques (>90% d'utilisation)
        critical_arcs = []
        for (source, dest), flow in self.results['flows'].items():
            for arc in self.network_data['arcs']:
                if arc['source'] == source and arc['destination'] == dest:
                    if arc['capacity'] > 0 and flow / arc['capacity'] > 0.9:
                        critical_arcs.append(f"{source}→{dest}")
                    break
        
        # Mettre à jour les labels
        self.total_flow_label.setText(f"{total_flow:,.2f} €")
        self.avg_cost_label.setText(f"{avg_cost:.4f} %")
        self.capacity_usage_label.setText(f"{avg_usage:.1f} %")
        self.critical_arcs_label.setText(f"{len(critical_arcs)}: {', '.join(critical_arcs[:3])}")
        
        # Générer des recommandations
        recommendations = self.generate_recommendations()
        self.recommendations_text.setText(recommendations)
    
    def generate_recommendations(self):
        """Génère des recommandations basées sur les résultats"""
        recommendations = []
        
        if self.results['objective'] > 0:
            recommendations.append("✅ Optimisation réussie")
        
        # Vérifier les capacités saturées
        for (source, dest), flow in self.results['flows'].items():
            for arc in self.network_data['arcs']:
                if arc['source'] == source and arc['destination'] == dest:
                    if arc['capacity'] > 0 and flow / arc['capacity'] > 0.95:
                        recommendations.append(
                            f"⚠️ Arc {source}→{dest} saturé à {(flow/arc['capacity']*100):.1f}%"
                        )
                    break
        
        # Recommandations générales
        if len(recommendations) == 1:
            recommendations.append("🌟 Excellent! Tous les transferts sont optimisés.")
        
        if self.results.get('status') == 'OPTIMAL':
            recommendations.append("📊 Solution optimale garantie par Gurobi")
        
        return '\n'.join(recommendations)
    
    def log_message(self, message):
        """Ajoute un message au journal"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{timestamp}] {message}")
    
    def export_results(self):
        """Exporte les résultats"""
        if not self.results:
            QMessageBox.warning(self, "Aucun résultat", 
                               "Aucun résultat à exporter. Résolvez d'abord le problème.")
            return
        
        # Sélectionner le fichier de destination
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exporter les résultats", 
            f"resultats_transferts_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel Files (*.xlsx);;CSV Files (*.csv);;JSON Files (*.json)"
        )
        
        if file_path:
            try:
                if file_path.endswith('.xlsx'):
                    self.export_to_excel(file_path)
                elif file_path.endswith('.csv'):
                    self.export_to_csv(file_path)
                elif file_path.endswith('.json'):
                    self.export_to_json(file_path)
                
                QMessageBox.information(self, "Export réussi", 
                                       f"Résultats exportés vers:\n{file_path}")
                self.log_message(f"📤 Résultats exportés: {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Erreur d'export", str(e))
    
    def export_to_excel(self, file_path):
        """Exporte les résultats vers Excel"""
        import pandas as pd
        
        # Créer un DataFrame pour les flux
        flows_data = []
        for (source, dest), flow in self.results['flows'].items():
            flows_data.append({
                'Source': source,
                'Destination': dest,
                'Flux (€)': flow,
                'Pourcentage du Total': (flow / sum(self.results['flows'].values())) * 100
            })
        
        flows_df = pd.DataFrame(flows_data)
        
        # Créer un DataFrame pour le résumé
        summary_data = [{
            'Date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'Coût Optimal (€)': self.results['objective'],
            'Temps de Résolution (s)': self.results['solving_time'],
            'Statut': self.results['status'],
            'Nombre d\'Arcs Actifs': len(self.results['flows'])
        }]
        
        summary_df = pd.DataFrame(summary_data)
        
        # Écrire dans Excel
        with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
            summary_df.to_excel(writer, sheet_name='Résumé', index=False)
            flows_df.to_excel(writer, sheet_name='Flux Détaillés', index=False)
            
            # Ajouter les paramètres du réseau
            params_df = pd.DataFrame([{
                'Nœuds': len(self.network_data['nodes']),
                'Arcs': len(self.network_data['arcs']),
                'Options Avancées': str({
                    'Risque': self.risk_checkbox.isChecked(),
                    'Multi-devises': self.multi_currency_checkbox.isChecked(),
                    'Contraintes Temps': self.time_constraint_checkbox.isChecked()
                })
            }])
            params_df.to_excel(writer, sheet_name='Paramètres', index=False)
    
    def export_to_csv(self, file_path):
        """Exporte les résultats vers CSV"""
        import pandas as pd
        
        flows_data = []
        for (source, dest), flow in self.results['flows'].items():
            flows_data.append({
                'source': source,
                'destination': dest,
                'flow': flow
            })
        
        df = pd.DataFrame(flows_data)
        df.to_csv(file_path, index=False)
    
    def export_to_json(self, file_path):
        """Exporte les résultats vers JSON"""
        export_data = {
            'timestamp': datetime.now().isoformat(),
            'results': self.results,
            'network': self.network_data,
            'supply_demand': self.supply_demand
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def save_visualization(self):
        """Sauvegarde la visualisation actuelle"""
        if not hasattr(self, 'viz_canvas'):
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Sauvegarder la visualisation", 
            f"visualisation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            "PNG Files (*.png);;PDF Files (*.pdf);;SVG Files (*.svg)"
        )
        
        if file_path:
            self.viz_canvas.figure.savefig(file_path, dpi=300, bbox_inches='tight')
            QMessageBox.information(self, "Sauvegarde réussie", 
                                   f"Visualisation sauvegardée:\n{file_path}")
            
    def add_node_row(self):
        """Ajoute une nouvelle ligne à la table des nœuds"""
        row = self.nodes_table.rowCount()
        self.nodes_table.insertRow(row)

        # Remplir avec des valeurs par défaut
        default_name = f"Banque_{row+1}_EUR"
        self.nodes_table.setItem(row, 0, QTableWidgetItem(default_name))
        self.nodes_table.setItem(row, 1, QTableWidgetItem("EUR"))
    
        # Type par défaut: Neutre
        type_combo = QComboBox()
        type_combo.addItems(["Neutre", "Offre (+)", "Demande (-)"])
        self.nodes_table.setCellWidget(row, 2, type_combo)
    
        # Valeur par défaut: 0
        self.nodes_table.setItem(row, 3, QTableWidgetItem("0"))
    
        self.log_message(f"➕ Nœud ajouté: {default_name}")

    def remove_node_row(self):
        """Supprime la ligne sélectionnée de la table des nœuds"""
        current_row = self.nodes_table.currentRow()
        if current_row >= 0:
            node_name = self.nodes_table.item(current_row, 0).text()
            self.nodes_table.removeRow(current_row)
            self.log_message(f"➖ Nœud supprimé: {node_name}")
            self.update_currency_summary()
        else:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez sélectionner un nœud à supprimer")

    def add_arc_row(self):
        """Ajoute une nouvelle ligne à la table des arcs"""
        row = self.arcs_table.rowCount()
        self.arcs_table.insertRow(row)
    
        # Remplir avec des valeurs par défaut
        if self.nodes_table.rowCount() > 0:
            first_node = self.nodes_table.item(0, 0).text()
            first_currency = self.nodes_table.item(0, 1).text() if self.nodes_table.item(0, 1) else "EUR"
        
            last_node = self.nodes_table.item(self.nodes_table.rowCount()-1, 0).text()
            last_currency = self.nodes_table.item(self.nodes_table.rowCount()-1, 1).text() \
                if self.nodes_table.item(self.nodes_table.rowCount()-1, 1) else "EUR"
        
            self.arcs_table.setItem(row, 0, QTableWidgetItem(first_node))
            self.arcs_table.setItem(row, 1, QTableWidgetItem(first_currency))
            self.arcs_table.setItem(row, 2, QTableWidgetItem(last_node))
            self.arcs_table.setItem(row, 3, QTableWidgetItem(last_currency))
        else:
            self.arcs_table.setItem(row, 0, QTableWidgetItem("BNP_EUR"))
            self.arcs_table.setItem(row, 1, QTableWidgetItem("EUR"))
            self.arcs_table.setItem(row, 2, QTableWidgetItem("SG_USD"))
            self.arcs_table.setItem(row, 3, QTableWidgetItem("USD"))
        
        self.arcs_table.setItem(row, 4, QTableWidgetItem("1.5"))
        self.arcs_table.setItem(row, 5, QTableWidgetItem("1000000"))
        
        # Checkbox activée par défaut
        checkbox = QCheckBox()
        checkbox.setChecked(True)
        self.arcs_table.setCellWidget(row, 6, checkbox)
        
        self.log_message("➕ Arc ajouté")

    def remove_arc_row(self):
        """Supprime la ligne sélectionnée de la table des arcs"""
        current_row = self.arcs_table.currentRow()
        if current_row >= 0:
            source = self.arcs_table.item(current_row, 0).text()
            dest = self.arcs_table.item(current_row, 2).text()
            self.arcs_table.removeRow(current_row)
            self.log_message(f"➖ Arc supprimé: {source} → {dest}")
        else:
            QMessageBox.warning(self, "Aucune sélection", "Veuillez sélectionner un arc à supprimer")

    def auto_fill_arcs(self):
        """Crée automatiquement des arcs entre toutes les combinaisons de nœuds"""
        if self.nodes_table.rowCount() < 2:
            QMessageBox.warning(self, "Pas assez de nœuds", "Ajoutez au moins 2 nœuds d'abord")
            return
        
        reply = QMessageBox.question(
            self, "Confirmation",
            f"Créer des arcs entre tous les {self.nodes_table.rowCount()} nœuds?\n"
            f"Cela générera {self.nodes_table.rowCount() * (self.nodes_table.rowCount() - 1)} arcs.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.arcs_table.setRowCount(0)
            
            nodes = []
            currencies = {}
            for i in range(self.nodes_table.rowCount()):
                node_name = self.nodes_table.item(i, 0).text()
                node_currency = self.nodes_table.item(i, 1).text() if self.nodes_table.item(i, 1) else "EUR"
                nodes.append((node_name, node_currency))
                currencies[node_name] = node_currency
            
            arc_count = 0
            for i, (src, src_curr) in enumerate(nodes):
                for j, (dest, dest_curr) in enumerate(nodes):
                    if i != j:  # Pas d'arc vers soi-même
                        row = self.arcs_table.rowCount()
                        self.arcs_table.insertRow(row)
                        
                        self.arcs_table.setItem(row, 0, QTableWidgetItem(src))
                        self.arcs_table.setItem(row, 1, QTableWidgetItem(src_curr))
                        self.arcs_table.setItem(row, 2, QTableWidgetItem(dest))
                        self.arcs_table.setItem(row, 3, QTableWidgetItem(dest_curr))
                        
                        # Coût par défaut basé sur si même devise ou non
                        default_cost = 1.0 if src_curr == dest_curr else 1.5
                        self.arcs_table.setItem(row, 4, QTableWidgetItem(f"{default_cost}"))
                        
                        # Capacité par défaut
                        self.arcs_table.setItem(row, 5, QTableWidgetItem("1000000"))
                        
                        # Checkbox activée
                        checkbox = QCheckBox()
                        checkbox.setChecked(True)
                        self.arcs_table.setCellWidget(row, 6, checkbox)
                        
                        arc_count += 1
            
            self.log_message(f"🔄 {arc_count} arcs générés automatiquement")

    def verify_data_consistency(self):
        """Vérifie la cohérence des données saisies"""
        errors = []
        warnings = []
        
        # Vérifier les nœuds
        if self.nodes_table.rowCount() == 0:
            errors.append("❌ Aucun nœud défini")
        else:
            node_names = set()
            for i in range(self.nodes_table.rowCount()):
                name_item = self.nodes_table.item(i, 0)
                currency_item = self.nodes_table.item(i, 1)
                value_item = self.nodes_table.item(i, 3)
                
                if name_item:
                    node_name = name_item.text()
                    if node_name in node_names:
                        errors.append(f"❌ Nœud dupliqué: {node_name}")
                    node_names.add(node_name)
                    
                    # Vérifier format avec devise
                    if '_' not in node_name:
                        warnings.append(f"⚠️ Nœud sans devise: {node_name} (format recommandé: Nom_DEVISE)")
                
                if currency_item and currency_item.text() not in ["EUR", "USD", "GBP", "CHF", "JPY"]:
                    warnings.append(f"⚠️ Devise non standard: {currency_item.text()}")
                
                if value_item:
                    try:
                        value = float(value_item.text().replace(',', ''))
                        if value < 0:
                            errors.append(f"❌ Valeur négative pour nœud {node_name}")
                    except ValueError:
                        errors.append(f"❌ Valeur invalide pour nœud {node_name}")
        
        # Vérifier les arcs
        if self.arcs_table.rowCount() == 0:
            warnings.append("⚠️ Aucun arc défini")
        else:
            for i in range(self.arcs_table.rowCount()):
                source_item = self.arcs_table.item(i, 0)
                dest_item = self.arcs_table.item(i, 2)
                cost_item = self.arcs_table.item(i, 4)
                capacity_item = self.arcs_table.item(i, 5)
                
                if source_item and dest_item:
                    source = source_item.text()
                    dest = dest_item.text()
                    
                    if source == dest:
                        errors.append(f"❌ Arc réflexif: {source} → {dest}")
                    
                    if source not in node_names:
                        errors.append(f"❌ Source inconnue: {source}")
                    if dest not in node_names:
                        errors.append(f"❌ Destination inconnue: {dest}")
                
                if cost_item:
                    try:
                        cost = float(cost_item.text())
                        if cost <= 0:
                            errors.append(f"❌ Coût négatif ou nul pour arc {i+1}")
                    except ValueError:
                        errors.append(f"❌ Coût invalide pour arc {i+1}")
                
                if capacity_item:
                    try:
                        capacity = float(capacity_item.text().replace(',', ''))
                        if capacity <= 0:
                            errors.append(f"❌ Capacité négative ou nulle pour arc {i+1}")
                    except ValueError:
                        errors.append(f"❌ Capacité invalide pour arc {i+1}")
        
        # Vérifier l'équilibre offre/demande
        total_supply = 0
        total_demand = 0
        
        for i in range(self.nodes_table.rowCount()):
            type_combo = self.nodes_table.cellWidget(i, 2)
            value_item = self.nodes_table.item(i, 3)
            
            if type_combo and value_item:
                try:
                    value = float(value_item.text().replace(',', ''))
                    if type_combo.currentIndex() == 1:  # Offre
                        total_supply += value
                    elif type_combo.currentIndex() == 2:  # Demande
                        total_demand += value
                except ValueError:
                    pass
        
        if total_supply != total_demand:
            warnings.append(f"⚠️ Déséquilibre offre/demande: Offre={total_supply:,.0f} ≠ Demande={total_demand:,.0f}")
        
        # Afficher les résultats
        self.verification_text.clear()
        
        if errors:
            self.verification_text.append("🚨 ERREURS:")
            for error in errors:
                self.verification_text.append(f"  {error}")
            self.verification_text.append("")
        
        if warnings:
            self.verification_text.append("⚠️ AVERTISSEMENTS:")
            for warning in warnings:
                self.verification_text.append(f"  {warning}")
            self.verification_text.append("")
        
        if not errors and not warnings:
            self.verification_text.append("✅ TOUT EST CORRECT!")
            self.verification_text.append(f"  • {len(node_names)} nœuds")
            self.verification_text.append(f"  • {self.arcs_table.rowCount()} arcs")
            self.verification_text.append(f"  • Offre totale: {total_supply:,.0f} €")
            self.verification_text.append(f"  • Demande totale: {total_demand:,.0f} €")
        
        # Colorer le texte
        if errors:
            self.verification_text.setStyleSheet("""
                QTextEdit {
                    background-color: #f8d7da;
                    border: 1px solid #f5c6cb;
                    color: #721c24;
                }
            """)
        elif warnings:
            self.verification_text.setStyleSheet("""
                QTextEdit {
                    background-color: #fff3cd;
                    border: 1px solid #ffeaa7;
                    color: #856404;
                }
            """)
        else:
            self.verification_text.setStyleSheet("""
                QTextEdit {
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    color: #155724;
                }
            """)
    
    def closeEvent(self, event):
        """Gère la fermeture de l'application"""
        reply = QMessageBox.question(
            self, 'Confirmation',
            'Êtes-vous sûr de vouloir quitter?',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            # Arrêter proprement les threads en cours
            if hasattr(self, 'solver_thread') and self.solver_thread.isRunning():
                self.solver_thread.terminate()
                self.solver_thread.wait()
            
            event.accept()
        else:
            event.ignore()