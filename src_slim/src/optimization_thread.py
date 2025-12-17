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
            
            # IMPORTANT: Nettoyer les attributs y_var avant de créer le modèle
            for ing in self.ingredients:
                if hasattr(ing, 'y_var'):
                    ing.y_var = None
                if hasattr(ing, 'x_var'):
                    ing.x_var = None
            
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
            
            # IMPORTANT: Ajouter d'abord les contraintes qui créent des variables binaires
            # (min_ingredients) avant celles qui les utilisent (min_proportion)
            
            if self.advanced_constraints.get('min_ingredients'):
                min_count = self.advanced_constraints.get('min_ingredients_count', 3)
                self.progress.emit(45, f"Ajout contrainte : min {min_count} ingrédients...")
                model.add_min_different_ingredients(min_count=min_count)
            
            if self.advanced_constraints.get('min_proportion'):
                ingredient_name = self.advanced_constraints.get('min_proportion_ingredient', 'Prémix vitamines')
                min_percent = self.advanced_constraints.get('min_proportion_percent', 2.0)
                self.progress.emit(50, f"Ajout contrainte : {ingredient_name} ≥ {min_percent}% si utilisé...")
                model.add_min_proportion_if_used(ingredient_name, min_percent)
            
            # Remises par quantité
            if self.advanced_constraints.get('quantity_discount'):
                ingredient_name = self.advanced_constraints.get('discount_ingredient', 'Maïs')
                discount_levels = [
                    (0, 100, 0.30),    # 0-100 kg à 0.30€/kg
                    (100, 500, 0.25),  # 100-500 kg à 0.25€/kg
                    (500, 10000, 0.20) # 500+ kg à 0.20€/kg
                ]
                self.progress.emit(55, f"Ajout remises pour {ingredient_name}...")
                model.add_quantity_discount(ingredient_name, discount_levels)
            
            # Balance énergétique
            if self.advanced_constraints.get('energy_balance'):
                ratios = {
                    'glucides': (0.4, 0.6),
                    'lipides': (0.2, 0.4)
                }
                self.progress.emit(60, "Ajout balance énergétique...")
                model.add_energy_balance_constraints(ratios)
            
            # Palatabilité
            if self.advanced_constraints.get('palatability'):
                self.progress.emit(65, "Ajout contrainte de palatabilité...")
                model.add_palatability_constraint()
            
            # Résoudre avec plus de temps pour PLM
            self.progress.emit(70, "Résolution avec Gurobi...")
            
            # Augmenter le temps limite si on a des contraintes PLM
            time_limit = self.time_limit
            if (self.advanced_constraints.get('min_ingredients') or 
                self.advanced_constraints.get('min_proportion') or
                self.advanced_constraints.get('quantity_discount')):
                time_limit = max(time_limit, 60)  # Au moins 60s pour PLM
            
            result = model.solve(time_limit=time_limit)
            
            self.progress.emit(100, "Optimisation terminée")
            self.finished.emit(result)
            
        except Exception as e:
            logger.error(f"Erreur dans le thread d'optimisation: {str(e)}", exc_info=True)
            self.error.emit(f"Erreur d'optimisation: {str(e)}")