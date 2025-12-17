# -*- coding: utf-8 -*-
"""
Created on Thu Dec 11 17:22:03 2025

@author: msi
"""
import os
# test_min_ingredients.py
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import gurobipy as gp
from gurobipy import GRB
from ingredients import Ingredient, NutritionalValues

print("="*70)
print("TEST ULTIME - ON DÉBOGUE TOUT")
print("="*70)

# 1. Créer un modèle MANUEL pour voir ce que Gurobi reçoit
print("\n1. CRÉATION MODÈLE MANUEL SIMPLE:")
model = gp.Model("Test_Manuel")

# 4 ingrédients, 3 pas chers, 1 très cher pour forcer 3 ingrédients
x1 = model.addVar(name="x_A", lb=0, ub=1000)  # prix 0.1
x2 = model.addVar(name="x_B", lb=0, ub=1000)  # prix 0.1  
x3 = model.addVar(name="x_C", lb=0, ub=1000)  # prix 0.1
x4 = model.addVar(name="x_D", lb=0, ub=1000)  # prix 100.0 (très cher!)

# Variables binaires y
y1 = model.addVar(vtype=GRB.BINARY, name="y_A")
y2 = model.addVar(vtype=GRB.BINARY, name="y_B")
y3 = model.addVar(vtype=GRB.BINARY, name="y_C")
y4 = model.addVar(vtype=GRB.BINARY, name="y_D")

# Objectif: minimiser coût (forcer D à 0 car cher)
model.setObjective(0.1*x1 + 0.1*x2 + 0.1*x3 + 100.0*x4, GRB.MINIMIZE)

# Contrainte: total = 1000 kg
model.addConstr(x1 + x2 + x3 + x4 == 1000, "total")

# Lier x et y avec Big M=1000
M = 1000
epsilon = 0.001

model.addConstr(x1 <= M * y1, "max_A")
model.addConstr(x1 >= epsilon * y1, "min_A")

model.addConstr(x2 <= M * y2, "max_B")
model.addConstr(x2 >= epsilon * y2, "min_B")

model.addConstr(x3 <= M * y3, "max_C")
model.addConstr(x3 >= epsilon * y3, "min_C")

model.addConstr(x4 <= M * y4, "max_D")
model.addConstr(x4 >= epsilon * y4, "min_D")

# CONTRAINTE TEST: au moins 3 y = 1
model.addConstr(y1 + y2 + y3 + y4 >= 3, "min_3_ingredients")

# Écrire le modèle
model.write("test_manuel.lp")
print("   Modèle écrit dans test_manuel.lp")

# Résoudre
print("\n2. RÉSOLUTION:")
model.optimize()

print(f"   Status: {model.status} ({GRB.OPTIMAL if model.status == GRB.OPTIMAL else 'NON OPTIMAL'})")

print("\n3. RÉSULTATS:")
print("   Variables x (quantités):")
print(f"   x_A = {x1.X:.3f} kg, y_A = {y1.X:.0f}")
print(f"   x_B = {x2.X:.3f} kg, y_B = {y2.X:.0f}")
print(f"   x_C = {x3.X:.3f} kg, y_C = {y3.X:.0f}")
print(f"   x_D = {x4.X:.3f} kg, y_D = {y4.X:.0f}")

y_sum = y1.X + y2.X + y3.X + y4.X
print(f"\n   Somme des y = {y_sum:.0f} (doit être ≥ 3)")

if y_sum >= 3:
    print("   ✅ CONTRAINTE RESPECTÉE DANS MODÈLE MANUEL")
else:
    print(f"   ❌ ERREUR: {y_sum} < 3 dans modèle manuel")
    print("   → Le problème est dans la LOGIQUE des contraintes")

print("\n" + "="*70)