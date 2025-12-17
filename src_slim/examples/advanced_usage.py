# -*- coding: utf-8 -*-
"""
Created on Mon Dec  8 08:53:37 2025

@author: msi
"""

#!/usr/bin/env python3
"""
Exemple avec contraintes PLM avancées.
Montre comment utiliser les contraintes complexes.
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ingredients import Ingredient, NutritionalValues
from blending_model import BlendingModel

def main():
    """Exemple avec contraintes PLM - ligne de commande."""
    print("=== EXEMPLE AVEC CONTRAINTES PLM (ADVANCÉ) ===\n")
    
    # 1. Créer des ingrédients avec propriétés avancées
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
                energie=3150.0
            ),
            disponibilite_max=200.0,
            indice_amertume=8.0,
            indice_sucrosite=1.0,
            antioxydants=200.0
        )
    ]
    
    print(f"Créé {len(ingredients)} ingrédients avec propriétés avancées")
    
    # 2. Créer le modèle
    model = BlendingModel()
    
    print("\n1. Construction du modèle de base...")
    model.create_basic_model(ingredients, Q_total=1000.0)
    
    print("2. Ajout des contraintes nutritionnelles...")
    requirements = {'proteines': (180.0, 220.0)}
    model.add_nutritional_constraints(requirements)
    
    print("3. Ajout des contraintes PLM avancées...")
    
    # Remises par quantité sur le maïs
    print("   • Remises par quantité (Maïs)")
    discount_levels = [
        (0, 100, 0.30),    # 0-100 kg à 0.30€/kg
        (100, 500, 0.25),  # 100-500 kg à 0.25€/kg
        (500, 1000, 0.20)  # 500+ kg à 0.20€/kg
    ]
    model.add_quantity_discount("Maïs", discount_levels)
    
    # Balance énergétique
    print("   • Balance énergétique (40-60% glucides)")
    ratios = {'glucides': (0.4, 0.6)}
    model.add_energy_balance_constraints(ratios)
    
    # Palatabilité
    print("   • Contrainte de palatabilité")
    model.add_palatability_constraint()
    
    # Saisonnalité (été)
    print("   • Contraintes saisonnières (été)")
    model.add_seasonal_constraints('ete')
    
    print("4. Résolution avec Gurobi...")
    result = model.solve(time_limit=15)
    
    # 3. Afficher les résultats
    print("\n" + "="*50)
    print("RÉSULTATS AVEC CONTRAINTES PLM")
    print("="*50)
    
    if result.success:
        print(f"✓ {result.message}")
        print(f"⏱️  Temps: {result.temps_resolution:.2f}s")
        print(f"💰 Coût: {result.cout_total:.2f} €")
        
        print("\n📦 COMPOSITION AVEC PLM:")
        print("-"*40)
        for nom, qty in result.quantites.items():
            if qty > 0.001:
                percent = (qty / 1000 * 100)
                print(f"  {nom:20} {qty:7.2f} kg ({percent:5.1f}%)")
        
    else:
        print(f"✗ {result.message}")
    
    print("\n" + "="*50)
    print("✅ Exemple PLM terminé!")

if __name__ == "__main__":
    main()