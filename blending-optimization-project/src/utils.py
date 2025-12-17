# -*- coding: utf-8 -*-
"""
Created on Mon Dec  8 08:33:12 2025

@author: msi
"""

"""
Fonctions utilitaires pour l'application.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Any

from ingredients import Ingredient, NutritionalValues

logger = logging.getLogger(__name__)

# Chemin vers les données
DATA_DIR = Path(__file__).parent.parent / "data"


def load_default_data() -> Tuple[List[Ingredient], Dict[str, Tuple[float, float]]]:
    """
    Charge les données par défaut depuis les fichiers JSON.
    
    Returns:
        Tuple (ingrédients, exigences nutritionnelles)
    """
    ingredients = load_default_ingredients()
    requirements = load_default_requirements()
    
    return ingredients, requirements


def load_default_ingredients() -> List[Ingredient]:
    """Charge la liste des ingrédients par défaut."""
    default_file = DATA_DIR / "default_ingredients.json"
    
    if not default_file.exists():
        # Créer des données par défaut si le fichier n'existe pas
        return create_sample_ingredients()
    
    try:
        with open(default_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        ingredients = []
        for item in data:
            nutrition = NutritionalValues(**item['nutrition'])
            ingredient = Ingredient(
                nom=item['nom'],
                cout=item['cout'],
                nutrition=nutrition,
                disponibilite_max=item['disponibilite_max'],
                indice_amertume=item.get('indice_amertume', 0.0),
                indice_sucrosite=item.get('indice_sucrosite', 0.0),
                antioxydants=item.get('antioxydants', 0.0),
                est_saisonnier=item.get('est_saisonnier', False),
                disponibilite_ete=item.get('disponibilite_ete'),
                disponibilite_hiver=item.get('disponibilite_hiver')
            )
            ingredients.append(ingredient)
        
        logger.info(f"{len(ingredients)} ingrédients chargés depuis {default_file}")
        return ingredients
        
    except Exception as e:
        logger.error(f"Erreur chargement ingrédients: {e}")
        return create_sample_ingredients()


def create_sample_ingredients() -> List[Ingredient]:
    """Crée un jeu d'ingrédients exemple."""
    ingredients = [
        Ingredient(
            nom="Maïs",
            cout=0.30,
            nutrition=NutritionalValues(
                proteines=85.0,
                lipides=40.0,
                glucides=700.0,
                fibres=20.0,
                calcium=0.2,
                phosphore=3.0,
                energie=3350.0
            ),
            disponibilite_max=1000.0,
            indice_amertume=2.0,
            indice_sucrosite=3.0,
            antioxydants=10.0,
            est_saisonnier=True,
            disponibilite_ete=1000.0,
            disponibilite_hiver=500.0
        ),
        Ingredient(
            nom="Tourteau de soja",
            cout=0.45,
            nutrition=NutritionalValues(
                proteines=480.0,
                lipides=20.0,
                glucides=300.0,
                fibres=60.0,
                calcium=3.0,
                phosphore=7.0,
                energie=2650.0
            ),
            disponibilite_max=500.0,
            indice_amertume=5.0,
            indice_sucrosite=1.0,
            antioxydants=50.0
        ),
        Ingredient(
            nom="Farine de poisson",
            cout=1.20,
            nutrition=NutritionalValues(
                proteines=650.0,
                lipides=80.0,
                glucides=10.0,
                fibres=10.0,
                calcium=50.0,
                phosphore=35.0,
                energie=3150.0
            ),
            disponibilite_max=200.0,
            indice_amertume=8.0,
            indice_sucrosite=1.0,
            antioxydants=200.0
        ),
        Ingredient(
            nom="Son de blé",
            cout=0.15,
            nutrition=NutritionalValues(
                proteines=160.0,
                lipides=40.0,
                glucides=550.0,
                fibres=120.0,
                calcium=1.0,
                phosphore=9.0,
                energie=2450.0
            ),
            disponibilite_max=300.0,
            indice_amertume=3.0,
            indice_sucrosite=2.0,
            antioxydants=30.0
        ),
        Ingredient(
            nom="Huile végétale",
            cout=0.80,
            nutrition=NutritionalValues(
                proteines=0.0,
                lipides=1000.0,
                glucides=0.0,
                fibres=0.0,
                calcium=0.0,
                phosphore=0.0,
                energie=9000.0
            ),
            disponibilite_max=100.0,
            indice_amertume=1.0,
            indice_sucrosite=0.0,
            antioxydants=100.0
        ),
        Ingredient(
            nom="Prémix vitamines",
            cout=5.00,
            nutrition=NutritionalValues(
                proteines=0.0,
                lipides=0.0,
                glucides=0.0,
                fibres=0.0,
                calcium=200.0,
                phosphore=100.0,
                energie=0.0
            ),
            disponibilite_max=50.0,
            indice_amertume=4.0,
            indice_sucrosite=0.0,
            antioxydants=1000.0
        ),
        Ingredient(
            nom="Carbonate de calcium",
            cout=0.10,
            nutrition=NutritionalValues(
                proteines=0.0,
                lipides=0.0,
                glucides=0.0,
                fibres=0.0,
                calcium=400.0,
                phosphore=0.0,
                energie=0.0
            ),
            disponibilite_max=100.0,
            indice_amertume=1.0,
            indice_sucrosite=0.0,
            antioxydants=0.0
        )
    ]
    
    logger.info(f"{len(ingredients)} ingrédients exemple créés")
    return ingredients


def load_default_requirements() -> Dict[str, Tuple[float, float]]:
    """Charge les exigences nutritionnelles par défaut."""
    default_file = DATA_DIR / "requirements.json"
    
    if not default_file.exists():
        return create_sample_requirements()
    
    try:
        with open(default_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        requirements = {}
        for item in data:
            requirements[item['nutrient']] = (item['min'], item['max'])
        
        logger.info(f"{len(requirements)} exigences chargées")
        return requirements
        
    except Exception as e:
        logger.error(f"Erreur chargement exigences: {e}")
        return create_sample_requirements()


def create_sample_requirements() -> Dict[str, Tuple[float, float]]:
    """Crée des exigences nutritionnelles exemple."""
    return {
        'proteines': (180.0, 220.0),      # g/kg
        'lipides': (30.0, 60.0),          # g/kg
        'glucides': (500.0, 700.0),       # g/kg
        'fibres': (20.0, 50.0),           # g/kg
        'calcium': (8.0, 12.0),           # g/kg
        'phosphore': (5.0, 8.0),          # g/kg
        'energie': (2800.0, 3200.0)       # kcal/kg
    }


def save_data(ingredients: List[Ingredient], 
              requirements: Dict[str, Tuple[float, float]]):
    """
    Sauvegarde les données dans des fichiers JSON.
    
    Args:
        ingredients: Liste des ingrédients
        requirements: Dict des exigences nutritionnelles
    """
    try:
        # Sauvegarder les ingrédients
        ingredients_data = [ing.to_dict() for ing in ingredients]
        with open(DATA_DIR / "saved_ingredients.json", 'w', encoding='utf-8') as f:
            json.dump(ingredients_data, f, indent=2, ensure_ascii=False)
        
        # Sauvegarder les exigences
        requirements_data = [
            {'nutrient': k, 'min': v[0], 'max': v[1]} 
            for k, v in requirements.items()
        ]
        with open(DATA_DIR / "saved_requirements.json", 'w', encoding='utf-8') as f:
            json.dump(requirements_data, f, indent=2, ensure_ascii=False)
        
        logger.info("Données sauvegardées avec succès")
        
    except Exception as e:
        logger.error(f"Erreur sauvegarde données: {e}")
        raise


def format_currency(amount: float) -> str:
    """Formate un montant en euros."""
    return f"{amount:,.2f} €".replace(",", " ")


def format_percentage(value: float) -> str:
    """Formate un pourcentage."""
    return f"{value:.1f} %"


def validate_ingredient_data(data: Dict[str, Any]) -> List[str]:
    """
    Valide les données d'un ingrédient.
    
    Returns:
        Liste des messages d'erreur (vide si valide)
    """
    errors = []
    
    if not data.get('nom') or not data['nom'].strip():
        errors.append("Le nom de l'ingrédient est requis")
    
    try:
        cout = float(data.get('cout', 0))
        if cout < 0:
            errors.append("Le coût ne peut pas être négatif")
    except ValueError:
        errors.append("Le coût doit être un nombre valide")
    
    try:
        dispo = float(data.get('disponibilite_max', 0))
        if dispo < 0:
            errors.append("La disponibilité ne peut pas être négative")
    except ValueError:
        errors.append("La disponibilité doit être un nombre valide")
    
    return errors