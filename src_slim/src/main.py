# -*- coding: utf-8 -*-
"""
Created on Mon Dec  8 08:29:44 2025

@author: msi
"""

#!/usr/bin/env python3
"""
Point d'entrée principal de l'application d'optimisation alimentaire.

"""

import sys
import logging
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """Fonction principale."""
    try:
        # Import ici pour éviter les problèmes de dépendances circulaires
        from main_window import MainWindow
        from utils import load_default_data
        
        logger.info("Démarrage de l'application d'optimisation alimentaire")
        
        # Créer l'application Qt
        app = QApplication(sys.argv)
        app.setApplicationName("Optimisation Alimentaire")
        app.setApplicationVersion("1.0.0")
        app.setAttribute(Qt.AA_EnableHighDpiScaling, True)
        
        # Charger les données par défaut
        default_ingredients, default_requirements = load_default_data()
        
        # Créer et afficher la fenêtre principale
        window = MainWindow(default_ingredients, default_requirements)
        window.show()
        
        logger.info("Interface graphique initialisée")
        
        # Exécuter la boucle d'événements
        return_code = app.exec_()
        
        logger.info(f"Application terminée (code: {return_code})")
        return return_code
        
    except Exception as e:
        logger.error(f"Erreur fatale: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())