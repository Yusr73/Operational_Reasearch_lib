# -*- coding: utf-8 -*-
"""
Created on Mon Dec  8 08:32:42 2025

@author: msi
"""

"""
Interface graphique principale de l'application.
Utilise PyQt5 pour une interface professionnelle.
"""

import sys
import logging
from typing import Dict, List, Tuple, Any

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QGroupBox, QLabel, QPushButton, QTableWidget, QTableWidgetItem,
    QSpinBox, QDoubleSpinBox, QComboBox, QCheckBox, QTextEdit,
    QProgressBar, QMessageBox, QHeaderView, QSplitter, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QBrush

import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure

from ingredients import Ingredient, NutritionalValues
from blending_model import OptimizationResult
from optimization_thread import OptimizationThread
from utils import load_default_data, save_data

logger = logging.getLogger(__name__)


class IngredientsTable(QTableWidget):
    """Widget table personnalisé pour la saisie des ingrédients."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Configure l'interface de la table."""
        headers = [
            "Ingrédient", "Coût (€/kg)", "Dispo max (kg)",
            "Protéines", "Lipides", "Glucides", "Fibres", 
            "Calcium", "Phosphore", "Énergie",
            "Amertume", "Sucrosité", "Antioxydants"
        ]
        
        self.setColumnCount(len(headers))
        self.setHorizontalHeaderLabels(headers)
        
        # Ajuster la largeur des colonnes
        header = self.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        for i in range(1, len(headers)):
            header.setSectionResizeMode(i, QHeaderView.ResizeToContents)
        
        # Style
        self.setAlternatingRowColors(True)
        self.setStyleSheet("""
            QTableWidget {
                alternate-background-color: #f0f0f0;
                background-color: white;
            }
            QTableWidget::item {
                padding: 5px;
            }
        """)
    
    def load_ingredients(self, ingredients: List[Ingredient]):
        """Charge les ingrédients dans la table."""
        self.setRowCount(len(ingredients))
        
        for row, ing in enumerate(ingredients):
            # Nom
            self.setItem(row, 0, QTableWidgetItem(ing.nom))
            
            # Coût
            cout_item = QTableWidgetItem(f"{ing.cout:.3f}")
            cout_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(row, 1, cout_item)
            
            # Disponibilité max
            dispo_item = QTableWidgetItem(f"{ing.disponibilite_max:.1f}")
            dispo_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(row, 2, dispo_item)
            
            # Valeurs nutritionnelles (g/kg)
            self.set_nutrition_item(row, 3, ing.nutrition.proteines)
            self.set_nutrition_item(row, 4, ing.nutrition.lipides)
            self.set_nutrition_item(row, 5, ing.nutrition.glucides)
            self.set_nutrition_item(row, 6, ing.nutrition.fibres)
            self.set_nutrition_item(row, 7, ing.nutrition.calcium)
            self.set_nutrition_item(row, 8, ing.nutrition.phosphore)
            
            # Énergie (kcal/kg)
            energie_item = QTableWidgetItem(f"{ing.nutrition.energie:.0f}")
            energie_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.setItem(row, 9, energie_item)
            
            # Indices de palatabilité
            self.set_item(row, 10, ing.indice_amertume)
            self.set_item(row, 11, ing.indice_sucrosite)
            
            # Antioxydants (mg/kg)
            self.set_item(row, 12, ing.antioxydants)
    
    def set_nutrition_item(self, row: int, col: int, value: float):
        """Définit un élément nutritionnel."""
        item = QTableWidgetItem(f"{value:.1f}")
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setItem(row, col, item)
    
    def set_item(self, row: int, col: int, value: float):
        """Définit un élément générique."""
        item = QTableWidgetItem(f"{value:.2f}")
        item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.setItem(row, col, item)
    
    def get_ingredients(self) -> List[Ingredient]:
        """Extrait les ingrédients depuis la table."""
        ingredients = []
        
        for row in range(self.rowCount()):
            try:
                nom = self.item(row, 0).text()
                cout = float(self.item(row, 1).text())
                dispo_max = float(self.item(row, 2).text())
                
                nutrition = NutritionalValues(
                    proteines=float(self.item(row, 3).text()),
                    lipides=float(self.item(row, 4).text()),
                    glucides=float(self.item(row, 5).text()),
                    fibres=float(self.item(row, 6).text()),
                    calcium=float(self.item(row, 7).text()),
                    phosphore=float(self.item(row, 8).text()),
                    energie=float(self.item(row, 9).text())
                )
                
                indice_amertume = float(self.item(row, 10).text())
                indice_sucrosite = float(self.item(row, 11).text())
                antioxydants = float(self.item(row, 12).text())
                
                ingredient = Ingredient(
                    nom=nom,
                    cout=cout,
                    nutrition=nutrition,
                    disponibilite_max=dispo_max,
                    indice_amertume=indice_amertume,
                    indice_sucrosite=indice_sucrosite,
                    antioxydants=antioxydants
                )
                
                ingredients.append(ingredient)
                
            except (AttributeError, ValueError) as e:
                logger.warning(f"Erreur lecture ligne {row}: {e}")
        
        return ingredients


class ResultsPlot(FigureCanvasQTAgg):
    """Widget pour afficher les résultats graphiquement."""
    
    def __init__(self, parent=None, width=8, height=6, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        
        self.ax1 = self.fig.add_subplot(221)  # Composition
        self.ax2 = self.fig.add_subplot(222)  # Coûts
        self.ax3 = self.fig.add_subplot(223)  # Nutrition
        self.ax4 = self.fig.add_subplot(224)  # Énergie
        
        self.fig.tight_layout()
    
    def update_plots(self, result: OptimizationResult):
        """Met à jour tous les graphiques avec les résultats."""
        self.fig.suptitle("Résultats de l'Optimisation", fontsize=14, fontweight='bold')
        
        # 1. Graphique de composition (camembert)
        self.ax1.clear()
        if result.pourcentages:
            labels = []
            sizes = []
            for nom, pourcent in result.pourcentages.items():
                if pourcent > 0.1:  # > 0.1%
                    labels.append(f"{nom}\n{pourcent:.1f}%")
                    sizes.append(pourcent)
            
            if sizes:
                self.ax1.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
                self.ax1.set_title('Composition du mélange')
            else:
                self.ax1.text(0.5, 0.5, 'Pas de données', 
                             ha='center', va='center', transform=self.ax1.transAxes)
        
        # 2. Graphique des coûts (barres)
        self.ax2.clear()
        if result.quantites:
            ingredients = list(result.quantites.keys())
            quantites = list(result.quantites.values())
            
            colors = plt.cm.Set3(range(len(ingredients)))
            bars = self.ax2.bar(ingredients, quantites, color=colors)
            
            self.ax2.set_title('Quantités optimales (kg)')
            self.ax2.set_xlabel('Ingrédients')
            self.ax2.set_ylabel('kg')
            self.ax2.tick_params(axis='x', rotation=45)
            
            # Ajouter les valeurs sur les barres
            for bar in bars:
                height = bar.get_height()
                self.ax2.text(bar.get_x() + bar.get_width()/2., height,
                             f'{height:.1f}', ha='center', va='bottom', fontsize=8)
        
        # 3. Graphique nutritionnel (radar)
        self.ax3.clear()
        if result.valeurs_nutritionnelles:
            nutrients = list(result.valeurs_nutritionnelles.keys())
            values = list(result.valeurs_nutritionnelles.values())
            
            # Normaliser pour le radar
            max_val = max(values) if values else 1
            values_norm = [v/max_val for v in values]
            
            angles = [n / float(len(nutrients)) * 2 * 3.14159 for n in range(len(nutrients))]
            values_norm += values_norm[:1]  # Fermer le polygone
            angles += angles[:1]
            
            self.ax3 = plt.subplot(223, polar=True)
            self.ax3.plot(angles, values_norm, 'o-', linewidth=2)
            self.ax3.fill(angles, values_norm, alpha=0.25)
            self.ax3.set_xticks(angles[:-1])
            self.ax3.set_xticklabels(nutrients)
            self.ax3.set_title('Profil nutritionnel', y=1.1)
        
        # 4. Répartition énergétique
        self.ax4.clear()
        if 'energie' in result.valeurs_nutritionnelles:
            energy_total = result.valeurs_nutritionnelles['energie'] * result.quantites.get('total', 1)
            
            # Calculer les contributions (simplifié)
            labels = ['Protéines', 'Lipides', 'Glucides']
            sizes = [0.3, 0.3, 0.4]  # Placeholder
            
            self.ax4.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            self.ax4.set_title('Répartition énergétique')
        
        self.fig.tight_layout()
        self.draw()


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application."""
    
    def __init__(self, default_ingredients: List[Ingredient], 
                 default_requirements: Dict[str, Tuple[float, float]]):
        super().__init__()
        
        self.ingredients = default_ingredients
        self.nutritional_requirements = default_requirements
        self.advanced_constraints = {}
        self.optimization_thread = None
        
        self.setup_ui()
        self.load_default_data()
        
        logger.info("Interface graphique initialisée")
    
    def setup_ui(self):
        """Configure l'interface graphique complète."""
        self.setWindowTitle("Optimisation de Formulation Alimentaire - Projet RO")
        self.setGeometry(100, 100, 1400, 900)
        
        # Widget central
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Layout principal
        main_layout = QVBoxLayout(central_widget)
        
        # Barre de titre
        title_label = QLabel("🥗 OPTIMISATION DE FORMULATION ALIMENTAIRE")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                color: #2c3e50;
                padding: 10px;
                background-color: #ecf0f1;
                border-radius: 5px;
            }
        """)
        main_layout.addWidget(title_label)
        
        # Splitter pour diviser la fenêtre
        splitter = QSplitter(Qt.Horizontal)
        
        # Partie gauche : Saisie des données
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Onglets pour différentes sections
        self.tabs = QTabWidget()
        
        # Onglet 1 : Ingrédients
        self.setup_ingredients_tab()
        
        # Onglet 2 : Exigences nutritionnelles
        self.setup_requirements_tab()
        
        # Onglet 3 : Contraintes avancées
        self.setup_advanced_constraints_tab()
        
        left_layout.addWidget(self.tabs)
        
        # Partie droite : Résultats
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        
        # Graphique des résultats
        self.results_plot = ResultsPlot(self, width=10, height=8)
        right_layout.addWidget(self.results_plot)
        
        # Zone de texte pour résultats détaillés
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        self.results_text.setMaximumHeight(200)
        self.results_text.setStyleSheet("""
            QTextEdit {
                background-color: #f8f9fa;
                border: 1px solid #dee2e6;
                font-family: 'Courier New', monospace;
                font-size: 10pt;
            }
        """)
        right_layout.addWidget(self.results_text)
        
        # Ajouter les widgets au splitter
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes([700, 700])
        
        main_layout.addWidget(splitter)
        
        # Barre de contrôle en bas
        control_bar = self.setup_control_bar()
        main_layout.addWidget(control_bar)
    
    def setup_ingredients_tab(self):
        """Configure l'onglet de saisie des ingrédients."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Table des ingrédients
        self.ingredients_table = IngredientsTable()
        layout.addWidget(self.ingredients_table)
        
        # Contrôles pour ajouter/supprimer des ingrédients
        control_layout = QHBoxLayout()
        
        btn_add = QPushButton("➕ Ajouter un ingrédient")
        btn_add.clicked.connect(self.add_ingredient_row)
        control_layout.addWidget(btn_add)
        
        btn_remove = QPushButton("➖ Supprimer la ligne sélectionnée")
        btn_remove.clicked.connect(self.remove_ingredient_row)
        control_layout.addWidget(btn_remove)
        
        btn_reset = QPushButton("🔄 Charger les données par défaut")
        btn_reset.clicked.connect(self.load_default_data)
        control_layout.addWidget(btn_reset)
        
        control_layout.addStretch()
        layout.addLayout(control_layout)
        
        self.tabs.addTab(tab, "Ingrédients")
    
    def setup_requirements_tab(self):
        """Configure l'onglet des exigences nutritionnelles."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Groupe pour la quantité totale
        qty_group = QGroupBox("Quantité totale à produire")
        qty_layout = QHBoxLayout()
        
        qty_layout.addWidget(QLabel("Quantité (kg):"))
        self.spin_qty_total = QSpinBox()
        self.spin_qty_total.setRange(100, 10000)
        self.spin_qty_total.setValue(1000)
        self.spin_qty_total.setSingleStep(100)
        qty_layout.addWidget(self.spin_qty_total)
        
        qty_layout.addStretch()
        qty_group.setLayout(qty_layout)
        layout.addWidget(qty_group)
        
        # Groupe pour les exigences nutritionnelles
        req_group = QGroupBox("Exigences nutritionnelles (g/kg de produit final)")
        req_layout = QVBoxLayout()
        
        # Table pour les exigences
        self.req_table = QTableWidget()
        self.req_table.setColumnCount(3)
        self.req_table.setHorizontalHeaderLabels(["Nutriment", "Minimum", "Maximum"])
        self.req_table.setRowCount(7)
        
        nutrients = [
            ("Protéines", 180, 220),
            ("Lipides", 30, 60),
            ("Glucides", 500, 700),
            ("Fibres", 20, 50),
            ("Calcium", 8, 12),
            ("Phosphore", 5, 8),
            ("Énergie (kcal/kg)", 2800, 3200)
        ]
        
        for row, (nutrient, min_val, max_val) in enumerate(nutrients):
            self.req_table.setItem(row, 0, QTableWidgetItem(nutrient))
            
            min_item = QTableWidgetItem(f"{min_val}")
            min_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.req_table.setItem(row, 1, min_item)
            
            max_item = QTableWidgetItem(f"{max_val}")
            max_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.req_table.setItem(row, 2, max_item)
        
        self.req_table.horizontalHeader().setStretchLastSection(True)
        req_layout.addWidget(self.req_table)
        req_group.setLayout(req_layout)
        layout.addWidget(req_group)
        
        layout.addStretch()
        self.tabs.addTab(tab, "Exigences nutritionnelles")
    
    def setup_advanced_constraints_tab(self):
        """Configure l'onglet des contraintes avancées."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Groupe pour les contraintes PLM
        constraints_group = QGroupBox("Contraintes Avancées (PLM)")
        constraints_layout = QVBoxLayout()
        
        # 1. Remises par quantité
        self.cb_discount = QCheckBox("Remises par quantité sur le Maïs")
        self.cb_discount.setToolTip("Prix dégressif selon la quantité achetée")
        constraints_layout.addWidget(self.cb_discount)
        
        # 2. Saisonnalité
        season_layout = QHBoxLayout()
        self.cb_seasonal = QCheckBox("Disponibilité saisonnière")
        self.cb_seasonal.setToolTip("Certains ingrédients disponibles selon la saison")
        season_layout.addWidget(self.cb_seasonal)
        
        season_layout.addWidget(QLabel("Saison:"))
        self.combo_season = QComboBox()
        self.combo_season.addItems(["Été", "Hiver"])
        season_layout.addWidget(self.combo_season)
        
        season_layout.addStretch()
        constraints_layout.addLayout(season_layout)
        
        # 3. Balance énergétique
        self.cb_energy = QCheckBox("Balance énergétique (40-60% glucides, 20-40% lipides)")
        self.cb_energy.setToolTip("Contraintes sur la répartition des sources d'énergie")
        constraints_layout.addWidget(self.cb_energy)
        
        # 4. Palatabilité
        self.cb_palatability = QCheckBox("Compensation amertume/sucrosité")
        self.cb_palatability.setToolTip("La sucrosité totale doit compenser l'amertume")
        constraints_layout.addWidget(self.cb_palatability)
        
        # 5. Durée de conservation
        self.cb_shelf_life = QCheckBox("Durée de conservation longue (>6 mois)")
        self.cb_shelf_life.setToolTip("Niveau minimal d'antioxydants requis")
        constraints_layout.addWidget(self.cb_shelf_life)
        
        # Explications
        explanation = QLabel(
            "⚠️ Ces contraintes utilisent des variables binaires (PLM) et "
            "complexifient le modèle. Sélectionnez uniquement celles nécessaires."
        )
        explanation.setWordWrap(True)
        explanation.setStyleSheet("color: #e74c3c; font-style: italic;")
        constraints_layout.addWidget(explanation)
        
        constraints_group.setLayout(constraints_layout)
        layout.addWidget(constraints_group)
        
        layout.addStretch()
        self.tabs.addTab(tab, "Contraintes avancées")
    
    def setup_control_bar(self) -> QFrame:
        """Configure la barre de contrôle en bas."""
        frame = QFrame()
        frame.setFrameStyle(QFrame.StyledPanel)
        layout = QHBoxLayout(frame)
        
        # Bouton d'optimisation
        self.btn_optimize = QPushButton("🚀 Lancer l'optimisation")
        self.btn_optimize.setFixedHeight(50)
        self.btn_optimize.setStyleSheet("""
            QPushButton {
                background-color: #27ae60;
                color: white;
                font-weight: bold;
                font-size: 14pt;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton:hover {
                background-color: #219653;
            }
            QPushButton:disabled {
                background-color: #95a5a6;
            }
        """)
        self.btn_optimize.clicked.connect(self.start_optimization)
        layout.addWidget(self.btn_optimize)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Bouton d'export
        btn_export = QPushButton("💾 Exporter les résultats")
        btn_export.clicked.connect(self.export_results)
        layout.addWidget(btn_export)
        
        # Bouton d'aide
        btn_help = QPushButton("❓ Aide")
        btn_help.clicked.connect(self.show_help)
        layout.addWidget(btn_help)
        
        return frame
    
    def load_default_data(self):
        """Charge les données par défaut."""
        try:
            self.ingredients_table.load_ingredients(self.ingredients)
            logger.info("Données par défaut chargées")
        except Exception as e:
            logger.error(f"Erreur chargement données: {e}")
            QMessageBox.critical(self, "Erreur", 
                               f"Impossible de charger les données: {str(e)}")
    
    def add_ingredient_row(self):
        """Ajoute une nouvelle ligne vide à la table des ingrédients."""
        row = self.ingredients_table.rowCount()
        self.ingredients_table.insertRow(row)
        
        # Remplir avec des valeurs par défaut
        self.ingredients_table.setItem(row, 0, QTableWidgetItem("Nouvel ingrédient"))
        
        for col in range(1, self.ingredients_table.columnCount()):
            item = QTableWidgetItem("0.0")
            item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.ingredients_table.setItem(row, col, item)
    
    def remove_ingredient_row(self):
        """Supprime la ligne sélectionnée."""
        current_row = self.ingredients_table.currentRow()
        if current_row >= 0:
            self.ingredients_table.removeRow(current_row)
    
    def get_nutritional_requirements(self) -> Dict[str, Tuple[float, float]]:
        """Extrait les exigences nutritionnelles depuis la table."""
        requirements = {}
        
        for row in range(self.req_table.rowCount()):
            try:
                nutrient = self.req_table.item(row, 0).text()
                min_val = float(self.req_table.item(row, 1).text())
                max_val = float(self.req_table.item(row, 2).text())
                
                requirements[nutrient.split()[0].lower()] = (min_val, max_val)
            except (AttributeError, ValueError):
                continue
        
        return requirements
    
    def get_advanced_constraints(self) -> Dict[str, Any]:
        """Récupère la configuration des contraintes avancées."""
        constraints = {}
        
        if self.cb_discount.isChecked():
            constraints['quantity_discount'] = True
            constraints['discount_ingredient'] = 'Maïs'
        
        if self.cb_seasonal.isChecked():
            constraints['seasonal'] = True
            constraints['season'] = 'ete' if self.combo_season.currentText() == 'Été' else 'hiver'
        
        if self.cb_energy.isChecked():
            constraints['energy_balance'] = True
        
        if self.cb_palatability.isChecked():
            constraints['palatability'] = True
        
        if self.cb_shelf_life.isChecked():
            constraints['shelf_life'] = True
        
        return constraints
    
    def start_optimization(self):
        """Démarre le processus d'optimisation dans un thread séparé."""
        # Récupérer les données
        try:
            self.ingredients = self.ingredients_table.get_ingredients()
            self.nutritional_requirements = self.get_nutritional_requirements()
            self.advanced_constraints = self.get_advanced_constraints()
            Q_total = self.spin_qty_total.value()
            
            if not self.ingredients:
                QMessageBox.warning(self, "Attention", "Aucun ingrédient saisi!")
                return
            
            # Désactiver le bouton pendant l'optimisation
            self.btn_optimize.setEnabled(False)
            self.btn_optimize.setText("⏳ Optimisation en cours...")
            
            # Afficher la barre de progression
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            
            # Créer et configurer le thread
            self.optimization_thread = OptimizationThread()
            self.optimization_thread.setup(
                ingredients=self.ingredients,
                Q_total=Q_total,
                nutritional_requirements=self.nutritional_requirements,
                advanced_constraints=self.advanced_constraints,
                time_limit=30
            )
            
            # Connecter les signaux
            self.optimization_thread.started.connect(self.on_optimization_started)
            self.optimization_thread.finished.connect(self.on_optimization_finished)
            self.optimization_thread.error.connect(self.on_optimization_error)
            self.optimization_thread.progress.connect(self.on_optimization_progress)
            
            # Démarrer le thread
            self.optimization_thread.start()
            
            logger.info("Optimisation démarrée")
            
        except Exception as e:
            logger.error(f"Erreur démarrage optimisation: {e}")
            QMessageBox.critical(self, "Erreur", f"Erreur de configuration: {str(e)}")
            self.btn_optimize.setEnabled(True)
    
    def on_optimization_started(self):
        """Appelé quand l'optimisation démarre."""
        self.results_text.clear()
        self.results_text.append("🚀 Démarrage de l'optimisation...")
        self.results_text.append(f"Nombre d'ingrédients: {len(self.ingredients)}")
        self.results_text.append(f"Quantité totale: {self.spin_qty_total.value()} kg")
        self.results_text.append("---")
    
    def on_optimization_progress(self, progress: int, message: str):
        """Met à jour la progression."""
        self.progress_bar.setValue(progress)
        self.results_text.append(f"[{progress}%] {message}")
    
    def on_optimization_finished(self, result: OptimizationResult):
        """Appelé quand l'optimisation est terminée."""
        # Réactiver l'interface
        self.btn_optimize.setEnabled(True)
        self.btn_optimize.setText("🚀 Lancer l'optimisation")
        self.progress_bar.setVisible(False)
        
        # Afficher les résultats
        self.display_results(result)
        
        # Mettre à jour les graphiques
        self.results_plot.update_plots(result)
        
        logger.info(f"Optimisation terminée: {result.message}")
    
    def on_optimization_error(self, error_message: str):
        """Appelé en cas d'erreur."""
        self.btn_optimize.setEnabled(True)
        self.btn_optimize.setText("🚀 Lancer l'optimisation")
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(self, "Erreur d'optimisation", error_message)
        self.results_text.append(f"❌ ERREUR: {error_message}")
        
        logger.error(f"Erreur optimisation: {error_message}")
    
    def display_results(self, result: OptimizationResult):
        """Affiche les résultats détaillés."""
        self.results_text.append("\n" + "="*50)
        self.results_text.append("📊 RÉSULTATS DE L'OPTIMISATION")
        self.results_text.append("="*50)
        
        if not result.success:
            self.results_text.append(f"❌ {result.message}")
            return
        
        self.results_text.append(f"✅ {result.message}")
        self.results_text.append(f"⏱️  Temps de résolution: {result.temps_resolution:.2f} secondes")
        self.results_text.append(f"🔄 Itérations: {result.iterations}")
        self.results_text.append(f"💰 Coût total: {result.cout_total:.2f} €")
        
        self.results_text.append("\n📦 COMPOSITION OPTIMALE:")
        self.results_text.append("-"*40)
        
        total_kg = sum(result.quantites.values())
        for nom, qty in result.quantites.items():
            pourcent = (qty / total_kg * 100) if total_kg > 0 else 0
            if qty > 0.001:  # > 1g
                self.results_text.append(f"  {nom:20} {qty:7.2f} kg ({pourcent:5.1f}%)")
        
        self.results_text.append("\n🥗 VALEURS NUTRITIONNELLES (g/kg):")
        self.results_text.append("-"*40)
        
        for nutriment, valeur in result.valeurs_nutritionnelles.items():
            self.results_text.append(f"  {nutriment:15} {valeur:7.2f}")
        
        # Afficher les prix duaux (shadow prices)
        if result.ombre_prix:
            self.results_text.append("\n📈 PRIX DUALS (contraintes actives):")
            self.results_text.append("-"*40)
            for constr, prix in result.ombre_prix.items():
                if abs(prix) > 1e-3:
                    self.results_text.append(f"  {constr:30} {prix:7.3f} €/unité")
    
    def export_results(self):
        """Exporte les résultats vers un fichier."""
        # Implémentation basique - à étendre
        QMessageBox.information(self, "Export", 
                              "Fonctionnalité d'export à implémenter")
    
    def show_help(self):
        """Affiche l'aide."""
        help_text = """
        <h2>Aide - Optimisation de Formulation Alimentaire</h2>
        
        <h3>📋 Utilisation de base:</h3>
        <ol>
        <li>Saisissez vos ingrédients dans l'onglet "Ingrédients"</li>
        <li>Définissez les exigences nutritionnelles</li>
        <li>Cliquez sur "Lancer l'optimisation"</li>
        <li>Visualisez les résultats dans la partie droite</li>
        </ol>
        
        <h3>🔧 Contraintes avancées (PLM):</h3>
        <ul>
        <li><b>Remises par quantité</b>: Prix dégressif selon la quantité achetée</li>
        <li><b>Saisonnalité</b>: Disponibilités différentes selon la saison</li>
        <li><b>Balance énergétique</b>: Ratio glucides/lipides fixé</li>
        <li><b>Palatabilité</b>: Compensation amertume par sucrosité</li>
        <li><b>Durée de conservation</b>: Niveau minimal d'antioxydants</li>
        </ul>
        
        <h3>⚙️ Solveur:</h3>
        <p>L'application utilise Gurobi, un solveur d'optimisation industriel.
        Une licence académique gratuite est nécessaire.</p>
        
        <h3>📊 Résultats:</h3>
        <p>Les résultats incluent:
        - Composition optimale du mélange
        - Coût total minimal
        - Vérification des contraintes
        - Prix duals (sensibilité)
        - Visualisations graphiques</p>
        """
        
        QMessageBox.information(self, "Aide", help_text)
    
    def closeEvent(self, event):
        """Gère la fermeture de l'application."""
        if self.optimization_thread and self.optimization_thread.isRunning():
            reply = QMessageBox.question(
                self, "Confirmation",
                "Une optimisation est en cours. Voulez-vous vraiment quitter?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.optimization_thread.terminate()
                self.optimization_thread.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()