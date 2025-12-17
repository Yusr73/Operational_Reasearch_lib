# -*- coding: utf-8 -*-
"""
Modèle principal CORRIGÉ - Toutes les contraintes PLM fonctionnent ensemble
"""

import gurobipy as gp
from gurobipy import GRB
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
import numpy as np

from ingredients import Ingredient

logger = logging.getLogger(__name__)

@dataclass
class OptimizationResult:
    """Contient tous les résultats d'une optimisation."""
    success: bool
    message: str
    cout_total: float
    quantites: Dict[str, float]
    pourcentages: Dict[str, float]
    valeurs_nutritionnelles: Dict[str, float]
    temps_resolution: float
    iterations: int
    status: str
    ombre_prix: Optional[Dict[str, float]] = None  # RÉTABLI
    couts_reduits: Optional[Dict[str, float]] = None  # RÉTABLI

class BlendingModel:
    """Modèle Gurobi pour l'optimisation de formulation alimentaire."""
    
    def __init__(self):
        """Initialise un nouveau modèle de mélange."""
        self.model = None
        self.ingredients = []
        self.Q_total = 1000.0
        self.binary_vars_registry = {}  # NOUVEAU : registre central des variables binaires
        
    def create_basic_model(self, ingredients: List[Ingredient], Q_total: float = 1000.0):
        """
        Crée le modèle PL de base.
        
        Args:
            ingredients: Liste des ingrédients disponibles
            Q_total: Quantité totale à produire (kg)
            
        Returns:
            Modèle Gurobi configuré
        """
        logger.info(f"Création du modèle PL de base pour {len(ingredients)} ingrédients")
        
        self.ingredients = ingredients
        self.Q_total = Q_total
        
        # Réinitialiser le registre
        self.binary_vars_registry = {}
        
        # Initialiser le modèle Gurobi
        self.model = gp.Model("Blending_Alimentaire")
        
        # 1. Variables de décision (quantités en kg)
        for ing in ingredients:
            ing.x_var = self.model.addVar(
                lb=0.0,
                ub=ing.disponibilite_max,
                vtype=GRB.CONTINUOUS,
                name=f"x_{ing.nom.replace(' ', '_')}"
            )
        
        # 2. Fonction objectif : minimiser le coût total
        cout_expr = gp.quicksum(ing.cout * ing.x_var for ing in ingredients)
        self.model.setObjective(cout_expr, GRB.MINIMIZE)
        
        # 3. Contrainte de base : quantité totale exacte
        total_expr = gp.quicksum(ing.x_var for ing in ingredients)
        self.model.addConstr(total_expr == Q_total, name="quantite_totale")
        
        logger.info("Modèle de base créé avec succès")
        return self.model
    
    def _get_binary_var(self, base_name: str, suffix: str = ""):
        """
        Récupère ou crée une variable binaire avec nom unique.
        Évite les doublons !
        """
        full_name = f"{base_name}_{suffix}" if suffix else base_name
        
        if full_name in self.binary_vars_registry:
            return self.binary_vars_registry[full_name]
        
        y_var = self.model.addVar(vtype=GRB.BINARY, name=full_name)
        self.binary_vars_registry[full_name] = y_var
        return y_var
    
    def add_nutritional_constraints(self, requirements: Dict[str, Tuple[float, float]]):
        """
        Ajoute les contraintes nutritionnelles au modèle.
        
        Args:
            requirements: Dict {nutriment: (min, max)} en g/kg de produit final
        """
        if not self.model:
            raise ValueError("Le modèle de base doit être créé d'abord")
        
        logger.info(f"Ajout de {len(requirements)} contraintes nutritionnelles")
        
        for nutriment, (min_val, max_val) in requirements.items():
            # Vérifier que le nutriment existe dans les ingrédients
            if not hasattr(self.ingredients[0].nutrition, nutriment):
                logger.warning(f"Nutriment '{nutriment}' non trouvé dans les ingrédients")
                continue
            
            # Construire l'expression pour ce nutriment
            nutr_expr = gp.quicksum(
                getattr(ing.nutrition, nutriment) * ing.x_var 
                for ing in self.ingredients
            )
            
            # Ajouter contraintes min et max
            if min_val is not None:
                self.model.addConstr(
                    nutr_expr >= min_val * self.Q_total,
                    name=f"min_{nutriment}"
                )
            
            if max_val is not None:
                self.model.addConstr(
                    nutr_expr <= max_val * self.Q_total,
                    name=f"max_{nutriment}"
                )
        
        logger.info("Contraintes nutritionnelles ajoutées")
    
    def add_quantity_discount(self, ingredient_name: str, discount_levels: List[Tuple[float, float, float]]):
        """
        Ajoute une structure de remise par quantité pour un ingrédient.
        
        Args:
            ingredient_name: Nom de l'ingrédient concerné
            discount_levels: Liste de (min, max, cout) pour chaque tranche
        """
        if not self.model:
            raise ValueError("Modèle non initialisé")
        
        # Trouver l'ingrédient
        ingredient = next((i for i in self.ingredients if i.nom == ingredient_name), None)
        if not ingredient:
            raise ValueError(f"Ingrédient '{ingredient_name}' non trouvé")
        
        logger.info(f"Ajout de remises par quantité pour {ingredient_name}")
        
        M = self.Q_total  # Valeur Big M
        
        # Variables binaires pour chaque tranche - utilisation du registre
        y_vars = []
        for j, (min_qty, max_qty, cout) in enumerate(discount_levels):
            y_var = self._get_binary_var(f"y_discount_{ingredient_name}", f"tranche{j}")
            y_vars.append(y_var)
        
        # Contrainte : une seule tranche active
        self.model.addConstr(gp.quicksum(y_vars) == 1, name=f"une_tranche_{ingredient_name}")
        
        # Variables pour la quantité dans chaque tranche
        x_tranches = []
        for j, (min_qty, max_qty, cout) in enumerate(discount_levels):
            x_t = self.model.addVar(lb=0, ub=max_qty, name=f"x_discount_{ingredient_name}_tranche{j}")
            x_tranches.append(x_t)
            
            # Contraintes de liaison
            self.model.addConstr(x_t <= max_qty * y_vars[j], 
                               name=f"max_tranche{j}_{ingredient_name}")
            self.model.addConstr(x_t >= min_qty * y_vars[j], 
                               name=f"min_tranche{j}_{ingredient_name}")
        
        # La quantité totale = somme des tranches
        self.model.addConstr(ingredient.x_var == gp.quicksum(x_tranches), 
                           name=f"total_discount_{ingredient_name}")
        
        # Modifier la fonction objectif
        old_obj = self.model.getObjective()
        
        # Construire un nouvel objectif
        new_obj_terms = []
        
        # Ajouter tous les ingrédients sauf celui avec remise
        for ing in self.ingredients:
            if ing.nom != ingredient_name:
                new_obj_terms.append(ing.cout * ing.x_var)
        
        # Ajouter les termes avec remises pour cet ingrédient
        for j, (_, _, cout) in enumerate(discount_levels):
            new_obj_terms.append(cout * x_tranches[j])
        
        # Mettre à jour l'objectif
        new_obj = gp.quicksum(new_obj_terms)
        self.model.setObjective(new_obj, GRB.MINIMIZE)
        
        logger.info(f"Remises ajoutées pour {ingredient_name}")
    
    def add_energy_balance_constraints(self, ratios: Dict[str, Tuple[float, float]]):
        """
        Ajoute des contraintes de balance énergétique.
        
        Args:
            ratios: Dict {'glucides': (0.4, 0.6), 'lipides': (0.2, 0.4)}
        """
        if not self.model:
            raise ValueError("Modèle non initialisé")
        
        logger.info("Ajout de contraintes de balance énergétique")
        
        # Calcul de l'énergie totale (kcal)
        energie_totale = gp.quicksum(
            ing.nutrition.energie * ing.x_var 
            for ing in self.ingredients
        )
        
        # Calcul de l'énergie par source
        energie_glucides = gp.quicksum(
            ing.nutrition.glucides * 4 * ing.x_var  # 4 kcal/g
            for ing in self.ingredients
        )
        
        energie_lipides = gp.quicksum(
            ing.nutrition.lipides * 9 * ing.x_var  # 9 kcal/g
            for ing in self.ingredients
        )
        
        # Contraintes de ratio
        if 'glucides' in ratios:
            min_ratio, max_ratio = ratios['glucides']
            self.model.addConstr(energie_glucides >= min_ratio * energie_totale, 
                               name="min_glucides_ratio")
            self.model.addConstr(energie_glucides <= max_ratio * energie_totale, 
                               name="max_glucides_ratio")
        
        if 'lipides' in ratios:
            min_ratio, max_ratio = ratios['lipides']
            self.model.addConstr(energie_lipides >= min_ratio * energie_totale, 
                               name="min_lipides_ratio")
            self.model.addConstr(energie_lipides <= max_ratio * energie_totale, 
                               name="max_lipides_ratio")
        
        logger.info("Contraintes de balance énergétique ajoutées")
    
    def add_palatability_constraint(self):
        """Ajoute une contrainte de palatabilité (sucrosité ≥ amertume)."""
        if not self.model:
            raise ValueError("Modèle non initialisé")
        
        logger.info("Ajout de contrainte de palatabilité")
        
        amertume_totale = gp.quicksum(
            ing.indice_amertume * ing.x_var 
            for ing in self.ingredients 
            if hasattr(ing, 'indice_amertume')
        )
        
        sucrosite_totale = gp.quicksum(
            ing.indice_sucrosite * ing.x_var 
            for ing in self.ingredients 
            if hasattr(ing, 'indice_sucrosite')
        )
        
        self.model.addConstr(sucrosite_totale >= amertume_totale, 
                           name="palatabilite")
        
        logger.info("Contrainte de palatabilité ajoutée")
    
    def add_min_different_ingredients(self, min_count=3):
        """
        Version SIMPLE et FONCTIONNELLE.
        Contrainte : au moins 'min_count' ingrédients différents dans le mélange.
        """
        if not self.model:
            raise ValueError("Modèle non initialisé")
        
        logger.info(f"Ajout contrainte : min {min_count} ingrédients différents")
        
        M = self.Q_total  # Grand M - valeur maximale possible
        epsilon = 0.001   # Valeur minimale pour dire "utilisé"
        
        # 1. Créer une variable binaire pour chaque ingrédient
        y_vars = []
        for ing in self.ingredients:
            # Nom unique : "y_min_ingredients_mais"
            var_name = f"y_min_ingredients_{ing.nom.replace(' ', '_')}"
            
            # Créer la variable binaire
            y = self.model.addVar(vtype=GRB.BINARY, name=var_name)
            y_vars.append(y)
            
            # 2. LIEN ENTRE x (continue) et y (binaire) :
            # Si y = 0 → x = 0
            # Si y = 1 → x >= epsilon (au moins un peu)
            
            # Contrainte 1 : x ≤ M * y (si y=0 alors x=0)
            self.model.addConstr(
                ing.x_var <= M * y,
                name=f"max_if_not_used_{ing.nom}"
            )
            
            # Contrainte 2 : x ≥ epsilon * y (si y=1 alors x≥epsilon)
            self.model.addConstr(
                ing.x_var >= epsilon * y,
                name=f"min_if_used_{ing.nom}"
            )
        
        # 3. CONTRAINTE PRINCIPALE : somme des y ≥ min_count
        self.model.addConstr(
            gp.quicksum(y_vars) >= min_count,
            name=f"min_different_ingredients"
        )
        
        logger.info(f"✓ Contrainte min_ingredients ajoutée (≥{min_count} ingrédients)")
        return True
    
    
    def add_min_proportion_if_used(self, ingredient_name: str, min_percent=2.0):
        """
        Si on utilise un ingrédient spécifique, on doit en mettre au moins X%.
        UTILISE LES MÊMES VARIABLES BINAIRES QUE add_min_different_ingredients
        """
        if not self.model:
            raise ValueError("Modèle non initialisé")
        
        logger.info(f"Ajout contrainte : {ingredient_name} ≥ {min_percent}% si utilisé")
        
        # Trouver l'ingrédient
        ingredient = next((i for i in self.ingredients if i.nom == ingredient_name), None)
        if not ingredient:
            raise ValueError(f"Ingrédient '{ingredient_name}' non trouvé")
        
        # Vérifier si la variable binaire existe déjà
        if f"y_active_{ingredient.nom}" not in self.binary_vars_registry:
            # Créer la variable binaire si elle n'existe pas
            y_var = self.model.addVar(vtype=GRB.BINARY, name=f"y_active_{ingredient.nom}")
            self.binary_vars_registry[f"y_active_{ingredient.nom}"] = y_var
            ingredient.y_var = y_var
            
            # Ajouter les contraintes de liaison x-y si elles n'existent pas
            M = self.Q_total
            epsilon = 0.001
            
            if f"max_active_{ingredient.nom}" not in [c.ConstrName for c in self.model.getConstrs()]:
                self.model.addConstr(ingredient.x_var <= M * y_var, 
                                   name=f"max_active_{ingredient.nom}")
            
            if f"min_active_{ingredient.nom}" not in [c.ConstrName for c in self.model.getConstrs()]:
                self.model.addConstr(ingredient.x_var >= epsilon * y_var,
                                   name=f"min_active_{ingredient.nom}")
        
        # Récupérer la variable binaire
        y_var = self.binary_vars_registry[f"y_active_{ingredient.nom}"]
        
        # Si utilisé (y=1), alors au moins min_percent%
        self.model.addConstr(
            ingredient.x_var >= (min_percent/100.0) * self.Q_total * y_var,
            name=f"min_percent_{ingredient.nom}"
        )
        
        logger.info(f"Contrainte min_proportion ajoutée pour {ingredient_name}")
        return True
    
    def solve(self, time_limit: int = 30) -> OptimizationResult:
        """
        Résout le modèle d'optimisation.
        
        Args:
            time_limit: Limite de temps en secondes
            
        Returns:
            OptimizationResult: Résultats de l'optimisation
        """
        if not self.model:
            raise ValueError("Modèle non initialisé")
        
        logger.info("Début de la résolution du modèle")
        
        # Configuration du solveur
        self.model.setParam('TimeLimit', time_limit)
        self.model.setParam('OutputFlag', 0)  # Désactiver la sortie console
        
        # Si le modèle contient des variables binaires (PLM), ajuster les paramètres
        if self.binary_vars_registry:
            self.model.setParam('MIPGap', 0.01)  # Tolérance de 1%
            self.model.setParam('MIPFocus', 1)   # Priorité à la faisabilité
            print(f"🔧 Modèle PLM détecté ({len(self.binary_vars_registry)} variables binaires)")
            print(f"🔧 Temps limite: {time_limit}s")
        
        # Résolution
        self.model.optimize()
        
        # Extraction des résultats
        result = self._extract_results()
        
        logger.info(f"Résolution terminée: {result.message} en {result.temps_resolution:.2f}s")
        return result
    
    def _extract_results(self) -> OptimizationResult:
        """Extrait les résultats du modèle résolu."""
        # Gérer les différents statuts
        status_messages = {
            GRB.OPTIMAL: ("Solution optimale trouvée", True),
            GRB.INFEASIBLE: ("Modèle infaisable", False),
            GRB.UNBOUNDED: ("Modèle non borné", False),
            GRB.TIME_LIMIT: ("Limite de temps atteinte", True),
            GRB.INTERRUPTED: ("Calcul interrompu", False)
        }
        
        status = self.model.status
        if status in status_messages:
            message, success = status_messages[status]
        else:
            message = f"Statut inattendu: {status}"
            success = False
        
        # Initialiser les structures de résultats
        quantites = {}
        pourcentages = {}
        valeurs_nutritionnelles = {}
        
        if success and hasattr(self.model, 'ObjVal'):
            cout_total = self.model.ObjVal
            
            # Récupérer les quantités
            for ing in self.ingredients:
                if hasattr(ing.x_var, 'X'):
                    qty = ing.x_var.X
                    if qty > 1e-6:  # Ignorer les très petites valeurs
                        quantites[ing.nom] = qty
                        pourcentages[ing.nom] = (qty / self.Q_total * 100) if self.Q_total > 0 else 0
            
            # Calculer les valeurs nutritionnelles finales
            if quantites:
                for attr in ['proteines', 'lipides', 'glucides', 'fibres', 'calcium', 'phosphore', 'energie']:
                    total = 0
                    for ing in self.ingredients:
                        if hasattr(ing.nutrition, attr) and ing.nom in quantites:
                            total += getattr(ing.nutrition, attr) * quantites[ing.nom]
                    valeurs_nutritionnelles[attr] = total / self.Q_total if self.Q_total > 0 else 0
        else:
            cout_total = 0
        ombre_prix = {}
        try:
            for constr in self.model.getConstrs():
                if  abs(constr.Pi) > 1e-6:
                    ombre_prix[constr.ConstrName] = constr.Pi
        except:
            ombre_prix = None
        
        # Récupérer les coûts réduits
        couts_reduits = {}
        try:
            for var in self.model.getVars():
                if abs(var.RC) > 1e-6:
                    couts_reduits[var.VarName] = var.RC
        except:
            couts_reduits = None
        
        return OptimizationResult(
            success=success,
            message=message,
            cout_total=cout_total,
            quantites=quantites,
            pourcentages=pourcentages,
            valeurs_nutritionnelles=valeurs_nutritionnelles,
            temps_resolution=self.model.Runtime if hasattr(self.model, 'Runtime') else 0,
            iterations=self.model.IterCount if hasattr(self.model, 'IterCount') else 0,
            status=str(status),
            ombre_prix=ombre_prix if ombre_prix else None,
            couts_reduits=couts_reduits if couts_reduits else None
        )
    
    def reset(self):
        """Réinitialise le modèle."""
        if self.model:
            self.model.dispose()
        self.model = None
        self.ingredients = []
        self.binary_vars_registry = {}
        logger.info("Modèle réinitialisé")        