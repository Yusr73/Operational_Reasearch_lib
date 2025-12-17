# -*- coding: utf-8 -*-
"""
Created on Mon Dec  8 08:46:47 2025

@author: msi
"""
"""
Tests pour l'interface graphique (nécessite pytest-qt).
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from PyQt5.QtWidgets import QApplication
from main_window import MainWindow
from ingredients import Ingredient, NutritionalValues

# Fixture pour l'application Qt
@pytest.fixture(scope="session")
def qapp():
    """Crée une application Qt pour les tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app

# Fixture pour la fenêtre principale
@pytest.fixture
def main_window(qapp):
    """Crée une fenêtre principale pour les tests."""
    # Créer des données de test minimales
    ingredients = [
        Ingredient(
            nom="Test1",
            cout=0.5,
            nutrition=NutritionalValues(proteines=100.0),
            disponibilite_max=1000.0
        )
    ]
    
    requirements = {'proteines': (150.0, 200.0)}
    
    window = MainWindow(ingredients, requirements)
    yield window
    window.close()

def test_window_creation(main_window):
    """Test que la fenêtre se crée correctement."""
    assert main_window is not None
    assert main_window.windowTitle() == "Optimisation de Formulation Alimentaire - Projet RO"

def test_ingredients_table(main_window):
    """Test la table des ingrédients."""
    table = main_window.ingredients_table
    assert table.rowCount() > 0
    assert table.columnCount() == 13  # Nombre de colonnes défini

def test_requirements_table(main_window):
    """Test la table des exigences nutritionnelles."""
    # La table des exigences devrait avoir des lignes
    req_table = main_window.req_table
    assert req_table.rowCount() == 7  # 7 nutriments par défaut

def test_advanced_constraints(main_window):
    """Test les cases à cocher des contraintes avancées."""
    # Vérifier que les checkboxes existent
    assert hasattr(main_window, 'cb_discount')
    assert hasattr(main_window, 'cb_energy')
    assert hasattr(main_window, 'cb_palatability')
    assert hasattr(main_window, 'cb_shelf_life')
    assert hasattr(main_window, 'cb_seasonal')
    
    # Par défaut, elles devraient être décochées
    assert not main_window.cb_discount.isChecked()
    assert not main_window.cb_energy.isChecked()

def test_optimization_button(main_window):
    """Test le bouton d'optimisation."""
    btn = main_window.btn_optimize
    assert btn is not None
    assert btn.text() == "🚀 Lancer l'optimisation"
    assert btn.isEnabled()
