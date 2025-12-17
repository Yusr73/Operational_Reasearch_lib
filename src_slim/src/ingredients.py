# -*- coding: utf-8 -*-
"""
Created on Mon Dec  8 08:31:18 2025

@author: msi
"""

"""
Définition des classes pour les ingrédients et leurs propriétés.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
import gurobipy as gp


@dataclass
class NutritionalValues:
    """Valeurs nutritionnelles pour 1 kg d'ingrédient."""
    proteines: float = 0.0  # g/kg
    lipides: float = 0.0    # g/kg
    glucides: float = 0.0   # g/kg
    fibres: float = 0.0     # g/kg
    calcium: float = 0.0    # g/kg
    phosphore: float = 0.0  # g/kg
    energie: float = 0.0    # kcal/kg


@dataclass
class Ingredient:
    """Représente un ingrédient pour le mélange alimentaire."""
    
    nom: str
    cout: float  # €/kg
    nutrition: NutritionalValues
    disponibilite_max: float  # kg maximum disponible
    
    # Propriétés pour contraintes avancées
    indice_amertume: float = 0.0  # 0-10
    indice_sucrosite: float = 0.0  # 0-10
    antioxydants: float = 0.0  # mg/kg
    
    # Propriétés saisonnières
    est_saisonnier: bool = False
    disponibilite_ete: Optional[float] = None
    disponibilite_hiver: Optional[float] = None
    
    # Variables Gurobi (initialisées plus tard)
    x_var: Optional[gp.Var] = None
    est_dans_modele: bool = False
    y_var: Optional[gp.Var] = None 
    
    def __post_init__(self):
        """Initialisation après création."""
        if self.disponibilite_ete is None:
            self.disponibilite_ete = self.disponibilite_max
        if self.disponibilite_hiver is None:
            self.disponibilite_hiver = self.disponibilite_max
    
    def to_dict(self) -> Dict:
        """Convertit l'ingrédient en dictionnaire pour sérialisation."""
        return {
            'nom': self.nom,
            'cout': self.cout,
            'disponibilite_max': self.disponibilite_max,
            'nutrition': {
                'proteines': self.nutrition.proteines,
                'lipides': self.nutrition.lipides,
                'glucides': self.nutrition.glucides,
                'fibres': self.nutrition.fibres,
                'calcium': self.nutrition.calcium,
                'phosphore': self.nutrition.phosphore,
                'energie': self.nutrition.energie
            },
            'indice_amertume': self.indice_amertume,
            'indice_sucrosite': self.indice_sucrosite,
            'antioxydants': self.antioxydants,
            'est_saisonnier': self.est_saisonnier,
            'disponibilite_ete': self.disponibilite_ete,
            'disponibilite_hiver': self.disponibilite_hiver
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Ingredient':
        """Crée un ingrédient à partir d'un dictionnaire."""
        nutrition = NutritionalValues(**data.get('nutrition', {}))
        ingredient = cls(
            nom=data['nom'],
            cout=data['cout'],
            nutrition=nutrition,
            disponibilite_max=data['disponibilite_max'],
            indice_amertume=data.get('indice_amertume', 0.0),
            indice_sucrosite=data.get('indice_sucrosite', 0.0),
            antioxydants=data.get('antioxydants', 0.0),
            est_saisonnier=data.get('est_saisonnier', False),
            disponibilite_ete=data.get('disponibilite_ete'),
            disponibilite_hiver=data.get('disponibilite_hiver')
        )
        
        # MAINTENANT initialiser y_var
        ingredient.y_var = None
        return ingredient
    