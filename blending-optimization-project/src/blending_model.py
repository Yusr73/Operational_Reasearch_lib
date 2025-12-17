# -*- coding: utf-8 -*-
"""
Created on Mon Dec  8 08:31:41 2025

@author: msi
"""

"""
Modèle principal de programmation linéaire pour l'optimisation de mélange.
Implémente PL de base et permet l'ajout de contraintes PLM.
"""

import gurobipy as gp
from gurobipy import GRB
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass

from ingredients import Ingredient

logger = logging.getLogger(__name__)


@dataclass
class OptimizationResult:
    """Contient tous les résultats d'une optimisation."""
    success: bool
    message: str
    cout_total: float
    quantites: Dict[str, float]  # kg de chaque ingrédient
    pourcentages: Dict[str, float]  # % de chaque ingrédient
    valeurs_nutritionnelles: Dict[str, float]
    temps_resolution: float
    iterations: int
    status: str
    ombre_prix: Optional[Dict[str, float]] = None
    couts_reduits: Optional[Dict[str, float]] = None


class BlendingModel:
    """Modèle Gurobi pour l'optimisation de formulation alimentaire."""
    
    def __init__(self):
        """Initialise un nouveau modèle de mélange."""
        self.model = None
        self.ingredients = []
        self.Q_total = 1000.0  # Quantité totale par défaut (kg)
        self.constraints_added = {
            'base': False,
            'nutrition': False,
            'quantity_discount': False,
            'seasonal': False,
            'energy_balance': False,
            'palatability': False,
            'shelf_life': False
        }
        
    def create_basic_model(self, ingredients: List[Ingredient], Q_total: float = 1000.0) -> gp.Model:
        """
        Crée le modèle PL de base (minimisation du coût).
        
        Args:
            ingredients: Liste des ingrédients disponibles
            Q_total: Quantité totale à produire (kg)
            
        Returns:
            Modèle Gurobi configuré
        """
        logger.info(f"Création du modèle PL de base pour {len(ingredients)} ingrédients")
        
        self.ingredients = ingredients
        self.Q_total = Q_total
        
        # Initialiser le modèle Gurobi
        self.model = gp.Model("Blending_Alimentaire")
        
        # 1. Variables de décision (quantités en kg)
        for ing in ingredients:
            ing.x_var = self.model.addVar(
                lb=0.0,
                ub=ing.disponibilite_max,
                vtype=GRB.CONTINUOUS,
                name=f"x_{ing.nom}"
            )
            ing.est_dans_modele = True
        
        # 2. Fonction objectif : minimiser le coût total
        cout_expr = gp.quicksum(ing.cout * ing.x_var for ing in ingredients)
        self.model.setObjective(cout_expr, GRB.MINIMIZE)
        
        # 3. Contrainte de base : quantité totale exacte
        total_expr = gp.quicksum(ing.x_var for ing in ingredients)
        self.model.addConstr(total_expr == Q_total, name="quantite_totale")
        
        self.constraints_added['base'] = True
        logger.info("Modèle de base créé avec succès")
        
        return self.model
    
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
        
        self.constraints_added['nutrition'] = True
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
        
        # Variables binaires pour chaque tranche
        y_vars = []
        for j, (min_qty, max_qty, cout) in enumerate(discount_levels):
            y = self.model.addVar(vtype=GRB.BINARY, name=f"y_{ingredient_name}_tranche{j}")
            y_vars.append(y)
        
        # Contrainte : une seule tranche active
        self.model.addConstr(gp.quicksum(y_vars) == 1, name=f"une_tranche_{ingredient_name}")
        
        # Variables pour la quantité dans chaque tranche
        x_tranches = []
        for j, (min_qty, max_qty, cout) in enumerate(discount_levels):
            x_t = self.model.addVar(lb=0, name=f"x_{ingredient_name}_tranche{j}")
            x_tranches.append(x_t)
            
            # Contraintes de liaison
            self.model.addConstr(x_t <= max_qty * y_vars[j], name=f"max_tranche{j}_{ingredient_name}")
            self.model.addConstr(x_t >= min_qty * y_vars[j], name=f"min_tranche{j}_{ingredient_name}")
        
        # La quantité totale = somme des tranches
        self.model.addConstr(ingredient.x_var == gp.quicksum(x_tranches), 
                           name=f"total_{ingredient_name}")
        
        # Modifier la fonction objectif pour prendre en compte les différents coûts
        old_obj = self.model.getObjective()
        new_terms = []
        
        # Récupérer tous les termes sauf celui de l'ingrédient
        for i in range(old_obj.size()):
            var = old_obj.getVar(i)
            coeff = old_obj.getCoeff(i)
            
            if var != ingredient.x_var:
                new_terms.append(coeff * var)
        
        # Ajouter les nouveaux termes avec remises
        for j, (_, _, cout) in enumerate(discount_levels):
            new_terms.append(cout * x_tranches[j])
        
        # Mettre à jour l'objectif
        new_obj = gp.quicksum(new_terms)
        self.model.setObjective(new_obj, GRB.MINIMIZE)
        
        self.constraints_added['quantity_discount'] = True
        logger.info(f"Remises ajoutées pour {ingredient_name}")
    
    def add_seasonal_constraints(self, season: str):
        """
        Ajoute des contraintes de saisonnalité.
        
        Args:
            season: 'ete' ou 'hiver'
        """
        if not self.model:
            raise ValueError("Modèle non initialisé")
        
        logger.info(f"Ajout de contraintes saisonnières pour {season}")
        
        # Variables binaires pour le choix de saison
        y_ete = self.model.addVar(vtype=GRB.BINARY, name="y_saison_ete")
        y_hiver = self.model.addVar(vtype=GRB.BINARY, name="y_saison_hiver")
        
        # Contrainte : choix exclusif
        self.model.addConstr(y_ete + y_hiver == 1, name="choix_saison_exclusif")
        
        # Appliquer les disponibilités selon la saison choisie
        for ing in self.ingredients:
            if ing.est_saisonnier:
                # Contrainte conditionnelle avec Big M
                M = self.Q_total
                
                # Si été choisi → x ≤ dispo_été
                self.model.addConstr(
                    ing.x_var <= ing.disponibilite_ete + M * (1 - y_ete),
                    name=f"dispo_ete_{ing.nom}"
                )
                
                # Si hiver choisi → x ≤ dispo_hiver
                self.model.addConstr(
                    ing.x_var <= ing.disponibilite_hiver + M * (1 - y_hiver),
                    name=f"dispo_hiver_{ing.nom}"
                )
        
        self.constraints_added['seasonal'] = True
        logger.info("Contraintes saisonnières ajoutées")
    
    def add_energy_balance_constraints(self, ratios: Dict[str, Tuple[float, float]]):
        """
        Ajoute des contraintes de balance énergétique.
        
        Args:
            ratios: Dict {'glucides': (0.4, 0.6), 'lipides': (0.2, 0.4)}
                     indiquant les pourcentages min/max d'énergie
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
        
        energie_proteines = gp.quicksum(
            ing.nutrition.proteines * 4 * ing.x_var  # 4 kcal/g
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
        
        # Vérification cohérence
        self.model.addConstr(
            energie_glucides + energie_lipides + energie_proteines == energie_totale,
            name="energie_totale_coherence"
        )
        
        self.constraints_added['energy_balance'] = True
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
        
        self.constraints_added['palatability'] = True
        logger.info("Contrainte de palatabilité ajoutée")
    
    def add_shelf_life_constraint(self, min_antioxidants: float):
        """
        Ajoute une contrainte de durée de conservation.
        
        Args:
            min_antioxidants: Minimum d'antioxydants requis (mg/kg)
        """
        if not self.model:
            raise ValueError("Modèle non initialisé")
        
        logger.info(f"Ajout de contrainte de durée de vie (min {min_antioxidants} mg/kg)")
        
        # Variable binaire : 1 = conservation longue activée
        y_conservation = self.model.addVar(vtype=GRB.BINARY, name="y_conservation_longue")
        
        # Total d'antioxydants
        total_antioxydants = gp.quicksum(
            ing.antioxydants * ing.x_var 
            for ing in self.ingredients 
            if hasattr(ing, 'antioxydants')
        )
        
        # Contrainte conditionnelle
        M = 1000000  # Grand M
        self.model.addConstr(
            total_antioxydants >= min_antioxidants * self.Q_total * y_conservation,
            name="shelf_life_antioxydants"
        )
        
        # Option : coût supplémentaire pour conservation
        # cost_term = 10 * y_conservation  # 10€ de coût fixe
        # old_obj = self.model.getObjective()
        # self.model.setObjective(old_obj + cost_term, GRB.MINIMIZE)
        
        self.constraints_added['shelf_life'] = True
        logger.info("Contrainte de durée de vie ajoutée")
    
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
        
        # Résolution
        self.model.optimize()
        
        # Extraction des résultats
        result = self._extract_results()
        
        logger.info(f"Résolution terminée: {result.message} en {result.temps_resolution:.2f}s")
        return result
    
    def _extract_results(self) -> OptimizationResult:
        """Extrait les résultats du modèle résolu."""
        if self.model.status == GRB.OPTIMAL:
            success = True
            message = "Solution optimale trouvée"
        elif self.model.status == GRB.INFEASIBLE:
            success = False
            message = "Modèle infaisable"
        elif self.model.status == GRB.UNBOUNDED:
            success = False
            message = "Modèle non borné"
        elif self.model.status == GRB.TIME_LIMIT:
            success = True
            message = "Limite de temps atteinte"
        else:
            success = False
            message = f"Statut inattendu: {self.model.status}"
        
        # Récupérer les quantités
        quantites = {}
        pourcentages = {}
        
        for ing in self.ingredients:
            if ing.est_dans_modele and hasattr(ing.x_var, 'X'):
                qty = ing.x_var.X
                quantites[ing.nom] = qty
                pourcentages[ing.nom] = (qty / self.Q_total * 100) if self.Q_total > 0 else 0
        
        # Calculer les valeurs nutritionnelles finales
        valeurs_nutritionnelles = {}
        if success and quantites:
            for attr in ['proteines', 'lipides', 'glucides', 'fibres', 'calcium', 'phosphore', 'energie']:
                total = sum(
                    getattr(ing.nutrition, attr) * quantites.get(ing.nom, 0)
                    for ing in self.ingredients
                )
                valeurs_nutritionnelles[attr] = total / self.Q_total if self.Q_total > 0 else 0
        
        # Récupérer les prix duaux (shadow prices)
        ombre_prix = {}
        try:
            for constr in self.model.getConstrs():
                if abs(constr.Pi) > 1e-6:  # Ignorer les valeurs très proches de 0
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
            cout_total=self.model.ObjVal if success else 0,
            quantites=quantites,
            pourcentages=pourcentages,
            valeurs_nutritionnelles=valeurs_nutritionnelles,
            temps_resolution=self.model.Runtime,
            iterations=self.model.IterCount,
            status=self.model.status,
            ombre_prix=ombre_prix,
            couts_reduits=couts_reduits
        )
    
    def reset(self):
        """Réinitialise le modèle."""
        if self.model:
            self.model.dispose()
        self.model = None
        self.ingredients = []
        self.constraints_added = {k: False for k in self.constraints_added}
        logger.info("Modèle réinitialisé")