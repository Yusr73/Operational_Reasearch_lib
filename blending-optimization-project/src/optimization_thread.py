# -*- coding: utf-8 -*-
"""
Created on Mon Dec  8 08:32:25 2025

@author: msi
"""

"""
Thread séparé pour exécuter l'optimisation sans bloquer l'interface.
"""

import logging
from PyQt5.QtCore import QThread, pyqtSignal
from blending_model import BlendingModel, OptimizationResult
from ingredients import Ingredient
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)


class OptimizationThread(QThread):
    """Thread pour exécuter l'optimisation en arrière-plan."""
    
    # Signaux pour communiquer avec l'interface
    started = pyqtSignal()
    finished = pyqtSignal(OptimizationResult)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, str)  # (pourcentage, message)
    
    def __init__(self, parent=None):
        """Initialise le thread d'optimisation."""
        super().__init__(parent)
        self.ingredients = []
        self.Q_total = 1000.0
        self.nutritional_requirements = {}
        self.advanced_constraints = {}
        self.time_limit = 30
        
    def setup(self, ingredients: List[Ingredient], Q_total: float,
              nutritional_requirements: Dict[str, Tuple[float, float]],
              advanced_constraints: Dict[str, Any], time_limit: int = 30):
        """Configure les paramètres d'optimisation."""
        self.ingredients = ingredients
        self.Q_total = Q_total
        self.nutritional_requirements = nutritional_requirements
        self.advanced_constraints = advanced_constraints
        self.time_limit = time_limit
    
    def run(self):
        """Méthode exécutée dans le thread."""
        try:
            self.started.emit()
            self.progress.emit(10, "Initialisation du modèle...")
            
            # Créer le modèle
            model = BlendingModel()
            
            # Construire le modèle de base
            self.progress.emit(20, "Construction du modèle PL de base...")
            model.create_basic_model(self.ingredients, self.Q_total)
            
            # Ajouter les contraintes nutritionnelles
            if self.nutritional_requirements:
                self.progress.emit(30, "Ajout des contraintes nutritionnelles...")
                model.add_nutritional_constraints(self.nutritional_requirements)
            
            # Ajouter les contraintes avancées
            self.progress.emit(40, "Ajout des contraintes avancées...")
            
            # Remises par quantité
            if self.advanced_constraints.get('quantity_discount'):
                ingredient_name = self.advanced_constraints.get('discount_ingredient', 'Maïs')
                discount_levels = [
                    (0, 100, 0.30),    # 0-100 kg à 0.30€/kg
                    (100, 500, 0.25),  # 100-500 kg à 0.25€/kg
                    (500, 10000, 0.20) # 500+ kg à 0.20€/kg
                ]
                model.add_quantity_discount(ingredient_name, discount_levels)
            
            # Saisonnalité
            if self.advanced_constraints.get('seasonal'):
                season = self.advanced_constraints.get('season', 'ete')
                model.add_seasonal_constraints(season)
            
            # Balance énergétique
            if self.advanced_constraints.get('energy_balance'):
                ratios = {
                    'glucides': (0.4, 0.6),
                    'lipides': (0.2, 0.4)
                }
                model.add_energy_balance_constraints(ratios)
            
            # Palatabilité
            if self.advanced_constraints.get('palatability'):
                model.add_palatability_constraint()
            
            # Durée de conservation
            if self.advanced_constraints.get('shelf_life'):
                model.add_shelf_life_constraint(min_antioxidants=50)  # 50 mg/kg
            
            # Résoudre
            self.progress.emit(60, "Résolution avec Gurobi...")
            result = model.solve(time_limit=self.time_limit)
            
            self.progress.emit(100, "Optimisation terminée")
            self.finished.emit(result)
            
        except Exception as e:
            logger.error(f"Erreur dans le thread d'optimisation: {str(e)}", exc_info=True)
            self.error.emit(f"Erreur d'optimisation: {str(e)}")