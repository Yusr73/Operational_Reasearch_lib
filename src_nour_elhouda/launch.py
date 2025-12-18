# src_nour_elhouda/launch.py - Version simple et directe

import sys
import os

# Définir le chemin du répertoire
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

# Fonction principale
def MainWindow():
    """Crée et retourne la fenêtre principale - format attendu par library.py"""
    
    # Vérifier que le fichier existe
    main_window_file = os.path.join(DIRECTORY, "main_window.py")
    if not os.path.exists(main_window_file):
        raise FileNotFoundError(f"Fichier main_window.py introuvable dans: {DIRECTORY}")
    
    # Ajouter le répertoire au path Python
    if DIRECTORY not in sys.path:
        sys.path.insert(0, DIRECTORY)
    
    try:
        # Importer PyQt6
        from PyQt6.QtWidgets import QApplication
        
        # Importer le module main_window
        import main_window
        
        # Créer l'application Qt si nécessaire
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Créer l'instance de MainWindow
        window_instance = main_window.MainWindow()
        
        return window_instance
        
    except ImportError as e:
        print(f"Erreur d'importation: {e}")
        print(f"Python path: {sys.path}")
        print(f"Fichier recherché: {main_window_file}")
        raise
        
    except Exception as e:
        print(f"Autre erreur: {e}")
        import traceback
        traceback.print_exc()
        raise


# Pour exécution directe
if __name__ == "__main__":
    try:
        window = MainWindow()
        if window:
            window.show()
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.exec()
    except Exception as e:
        print(f"Erreur: {e}")
        input("Appuyez sur Entrée pour quitter...")