# src/main.py
"""
Point d'entrée principal de l'application de flux à coût minimum pour les transferts financiers.
Problème 14 - Application 2 : Finance
"""

import sys
import os
import json
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import QFont
from main_window import MainWindow
import warnings

# Supprimer les warnings Gurobi
warnings.filterwarnings("ignore")

def create_sample_tests():
    """Crée des fichiers de test d'exemple si le dossier data est vide"""
    data_dir = "data"
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    # Vérifier si des tests existent déjà
    existing_tests = [f for f in os.listdir(data_dir) if f.endswith('.json')]
    
    if existing_tests:
        return  # Ne pas écraser les tests existants
    
    # Créer les 3 fichiers de test
    tests = [
        {
            "filename": "test_simple.json",
            "data": {
                "name": "Test Simple - 3 Banques",
                "description": "Test simple avec 3 banques et équilibre offre/demande",
                "network_data": {
                    "nodes": ["BNP_EUR", "SG_USD", "HSBC_GBP"],
                    "arcs": [
                        {"source": "BNP_EUR", "destination": "SG_USD", "cost": 1.5, "capacity": 500000},
                        {"source": "SG_USD", "destination": "HSBC_GBP", "cost": 2.0, "capacity": 300000},
                        {"source": "BNP_EUR", "destination": "HSBC_GBP", "cost": 2.5, "capacity": 400000}
                    ]
                },
                "supply_demand": {
                    "BNP_EUR": 600000,
                    "SG_USD": -200000,
                    "HSBC_GBP": -400000
                },
                "options": {
                    "include_risk": False,
                    "multi_currency": False,
                    "time_constraints": False
                }
            }
        },
        {
            "filename": "test_complexe.json",
            "data": {
                "name": "Test Complexe - 6 Banques Multi-devises",
                "description": "Test complexe avec plusieurs devises et contraintes",
                "network_data": {
                    "nodes": ["BNP_EUR", "SG_USD", "HSBC_GBP", "Deutsche_EUR", "JPMorgan_USD", "Barclays_GBP"],
                    "arcs": [
                        {"source": "BNP_EUR", "destination": "SG_USD", "cost": 1.5, "capacity": 1000000},
                        {"source": "SG_USD", "destination": "HSBC_GBP", "cost": 2.0, "capacity": 800000},
                        {"source": "HSBC_GBP", "destination": "Deutsche_EUR", "cost": 1.8, "capacity": 600000},
                        {"source": "Deutsche_EUR", "destination": "JPMorgan_USD", "cost": 1.2, "capacity": 900000},
                        {"source": "JPMorgan_USD", "destination": "Barclays_GBP", "cost": 2.5, "capacity": 700000},
                        {"source": "BNP_EUR", "destination": "Deutsche_EUR", "cost": 0.5, "capacity": 1500000},
                        {"source": "SG_USD", "destination": "JPMorgan_USD", "cost": 0.8, "capacity": 1200000},
                        {"source": "HSBC_GBP", "destination": "Barclays_GBP", "cost": 0.3, "capacity": 500000},
                        {"source": "BNP_EUR", "destination": "Barclays_GBP", "cost": 3.0, "capacity": 400000},
                        {"source": "Deutsche_EUR", "destination": "HSBC_GBP", "cost": 2.2, "capacity": 550000}
                    ]
                },
                "supply_demand": {
                    "BNP_EUR": 1500000,
                    "SG_USD": 500000,
                    "HSBC_GBP": 0,
                    "Deutsche_EUR": 0,
                    "JPMorgan_USD": -800000,
                    "Barclays_GBP": -1200000
                },
                "options": {
                    "include_risk": True,
                    "multi_currency": True,
                    "time_constraints": True
                }
            }
        },
        {
            "filename": "test_infaisable.json",
            "data": {
                "name": "Test Infaisable - Offre < Demande",
                "description": "Test avec offre insuffisante pour couvrir la demande",
                "network_data": {
                    "nodes": ["BNP_EUR", "SG_USD", "HSBC_GBP", "Deutsche_EUR"],
                    "arcs": [
                        {"source": "BNP_EUR", "destination": "SG_USD", "cost": 1.5, "capacity": 500000},
                        {"source": "SG_USD", "destination": "HSBC_GBP", "cost": 2.0, "capacity": 300000},
                        {"source": "Deutsche_EUR", "destination": "HSBC_GBP", "cost": 1.8, "capacity": 200000}
                    ]
                },
                "supply_demand": {
                    "BNP_EUR": 300000,
                    "SG_USD": 0,
                    "HSBC_GBP": -800000,
                    "Deutsche_EUR": 200000
                },
                "options": {
                    "include_risk": False,
                    "multi_currency": False,
                    "time_constraints": False
                }
            }
        }
    ]
    
    # Écrire les fichiers
    for test in tests:
        filepath = os.path.join(data_dir, test["filename"])
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(test["data"], f, indent=2, ensure_ascii=False)
    
    print(f"✅ 3 fichiers de test créés dans le dossier '{data_dir}/'")

def main():
    """Fonction principale de l'application"""
    # Créer les tests d'exemple
    create_sample_tests()
    
    app = QApplication(sys.argv)
    
    # Configuration du style global
    app.setStyle("Fusion")
    
    # Configuration de la police
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Création de la fenêtre principale
    window = MainWindow()
    window.show()
    
    # Lancement de l'application
    sys.exit(app.exec())

if __name__ == "__main__":
    main()