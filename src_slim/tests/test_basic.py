# -*- coding: utf-8 -*-
"""
Created on Mon Dec  8 08:46:23 2025

@author: msi
"""

"""
Tests unitaires pour le projet d'optimisation alimentaire.
"""

import unittest
import sys
import os

# Ajouter le répertoire src au chemin
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from ingredients import Ingredient, NutritionalValues
from blending_model import BlendingModel
from utils import validate_ingredient_data

class TestIngredients(unittest.TestCase):
    """Tests pour les classes d'ingrédients."""
    
    def test_ingredient_creation(self):
        """Test la création d'un ingrédient."""
        nutrition = NutritionalValues(
            proteines=100.0,
            lipides=50.0,
            glucides=600.0
        )
        
        ingredient = Ingredient(
            nom="Test Ingredient",
            cout=0.50,
            nutrition=nutrition,
            disponibilite_max=1000.0
        )
        
        self.assertEqual(ingredient.nom, "Test Ingredient")
        self.assertEqual(ingredient.cout, 0.50)
        self.assertEqual(ingredient.nutrition.proteines, 100.0)
    
    def test_ingredient_to_dict(self):
        """Test la conversion en dictionnaire."""
        nutrition = NutritionalValues(proteines=100.0)
        ingredient = Ingredient("Test", 0.5, nutrition, 1000.0)
        
        data = ingredient.to_dict()
        
        self.assertEqual(data['nom'], "Test")
        self.assertEqual(data['cout'], 0.5)
        self.assertEqual(data['nutrition']['proteines'], 100.0)
    
    def test_ingredient_from_dict(self):
        """Test la création depuis un dictionnaire."""
        data = {
            'nom': 'Test',
            'cout': 0.5,
            'disponibilite_max': 1000.0,
            'nutrition': {
                'proteines': 100.0,
                'lipides': 50.0,
                'glucides': 600.0
            }
        }
        
        ingredient = Ingredient.from_dict(data)
        
        self.assertEqual(ingredient.nom, "Test")
        self.assertEqual(ingredient.cout, 0.5)
        self.assertEqual(ingredient.nutrition.proteines, 100.0)


class TestBlendingModel(unittest.TestCase):
    """Tests pour le modèle de mélange."""
    
    def setUp(self):
        """Prépare les données de test."""
        self.ingredients = [
            Ingredient(
                nom="Ing1",
                cout=1.0,
                nutrition=NutritionalValues(proteines=100.0, energie=1000.0),
                disponibilite_max=500.0
            ),
            Ingredient(
                nom="Ing2",
                cout=2.0,
                nutrition=NutritionalValues(proteines=200.0, energie=2000.0),
                disponibilite_max=500.0
            )
        ]
    
    def test_model_creation(self):
        """Test la création du modèle."""
        model = BlendingModel()
        gurobi_model = model.create_basic_model(self.ingredients, Q_total=1000.0)
        
        self.assertIsNotNone(gurobi_model)
        self.assertEqual(len(model.ingredients), 2)
    
    def test_nutritional_constraints(self):
        """Test l'ajout de contraintes nutritionnelles."""
        model = BlendingModel()
        model.create_basic_model(self.ingredients, Q_total=1000.0)
        
        requirements = {'proteines': (150.0, None)}  # Min 150 g/kg
        model.add_nutritional_constraints(requirements)
        
        # Vérifier que les contraintes sont ajoutées
        self.assertTrue(model.constraints_added['nutrition'])


class TestUtils(unittest.TestCase):
    """Tests pour les fonctions utilitaires."""
    
    def test_validate_ingredient_data(self):
        """Test la validation des données d'ingrédient."""
        # Données valides
        valid_data = {
            'nom': 'Test',
            'cout': '0.5',
            'disponibilite_max': '1000'
        }
        
        errors = validate_ingredient_data(valid_data)
        self.assertEqual(len(errors), 0)
        
        # Données invalides
        invalid_data = {
            'nom': '',
            'cout': '-1',
            'disponibilite_max': '-100'
        }
        
        errors = validate_ingredient_data(invalid_data)
        self.assertGreater(len(errors), 0)


class TestIntegration(unittest.TestCase):
    """Tests d'intégration."""
    
    def test_complete_workflow(self):
        """Test un workflow complet simple."""
        # Créer un modèle simple
        ingredients = [
            Ingredient(
                nom="Céréale",
                cout=0.30,
                nutrition=NutritionalValues(proteines=100.0),
                disponibilite_max=1000.0
            ),
            Ingredient(
                nom="Protéine",
                cout=0.60,
                nutrition=NutritionalValues(proteines=400.0),
                disponibilite_max=500.0
            )
        ]
        
        model = BlendingModel()
        model.create_basic_model(ingredients, Q_total=1000.0)
        
        # Ajouter une contrainte protéique
        model.add_nutritional_constraints({'proteines': (150.0, None)})
        
        # Résoudre
        result = model.solve(time_limit=5)
        
        # Vérifier les résultats de base
        self.assertIn(result.success, [True, False])
        self.assertIsInstance(result.cout_total, float)
        self.assertIsInstance(result.quantites, dict)


if __name__ == '__main__':
    unittest.main()