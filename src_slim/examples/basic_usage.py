# -*- coding: utf-8 -*-
"""
Created on Mon Dec  8 08:53:14 2025

@author: msi
"""

#!/usr/bin/env python3
"""
Exemple d'utilisation en ligne de commande de l'optimiseur.
Sans interface graphique - purement Python.
"""

import sys
import os

# Ajouter le répertoire src au chemin
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ingredients import Ingredient, NutritionalValues
from blending_model import BlendingModel

def main():
    """Exemple d'optimisation simple sans interface graphique."""
    print("=== EXEMPLE D'OPTIMISATION ALIMENTAIRE (LIGNE DE COMMANDE) ===\n")
    
    # 1. Créer des ingrédients de test
    ingredients = [
        Ingredient(
            nom="Maïs",
            cout=0.30,
            nutrition=NutritionalValues(
                proteines=85.0,
                lipides=40.0,
                glucides=700.0,
                energie=3350.0
            ),
            disponibilite_max=1000.0
        ),
        Ingredient(
            nom="Tourteau de soja",
            cout=0.45,
            nutrition=NutritionalValues(
                proteines=480.0,
                lipides=20.0,
                glucides=300.0,
                energie=2650.0
            ),
            disponibilite_max=500.0
        ),
        Ingredient(
            nom="Son de blé",
            cout=0.15,
            nutrition=NutritionalValues(
                proteines=160.0,
                lipides=40.0,
                glucides=550.0,
                energie=2450.0
            ),
            disponibilite_max=300.0
        )
    ]
    
    print(f"Créé {len(ingredients)} ingrédients")
    
    # 2. Créer et configurer le modèle
    model = BlendingModel()
    
    print("\n1. Construction du modèle PL de base...")
    model.create_basic_model(ingredients, Q_total=1000.0)
    
    print("2. Ajout des contraintes nutritionnelles...")
    requirements = {
        'proteines': (180.0, 220.0),  # 180-220 g/kg
        'energie': (2800.0, 3200.0)   # 2800-3200 kcal/kg
    }
    model.add_nutritional_constraints(requirements)
    
    print("3. Résolution avec Gurobi...")
    result = model.solve(time_limit=10)
    
    # 3. Afficher les résultats
    print("\n" + "="*50)
    print("RÉSULTATS DE L'OPTIMISATION")
    print("="*50)
    
    if result.success:
        print(f"✓ {result.message}")
        print(f"⏱️  Temps de résolution: {result.temps_resolution:.2f}s")
        print(f"💰 Coût total: {result.cout_total:.2f} €")
        print(f"📊 Nombre d'itérations: {result.iterations}")
        
        print("\n📦 COMPOSITION OPTIMALE:")
        print("-"*40)
        for nom, qty in result.quantites.items():
            if qty > 0.001:
                percent = result.pourcentages[nom]
                print(f"  {nom:20} {qty:7.2f} kg ({percent:5.1f}%)")
        
        print("\n🥗 VALEURS NUTRITIONNELLES FINALES:")
        print("-"*40)
        for nutriment, valeur in result.valeurs_nutritionnelles.items():
            print(f"  {nutriment:15} {valeur:7.2f} g/kg")
        
    else:
        print(f"✗ {result.message}")
    
    print("\n" + "="*50)
    print("Exemple terminé avec succès!")

if __name__ == "__main__":
    main()