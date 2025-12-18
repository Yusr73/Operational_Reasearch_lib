# launch.py - Version pour structure: src_nour_elhouda/launch.py et src_nour_elhouda/src/main_window.py
import sys
import os

# Chemin vers le répertoire courant (src_nour_elhouda)
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
# Chemin vers le sous-dossier src
SRC_DIR = os.path.join(CURRENT_DIR, "src")

def MainWindow():
    """Crée et retourne la fenêtre principale - format attendu par library.py"""
    
    # Debug: Afficher les chemins
    print(f"Dossier courant: {CURRENT_DIR}")
    print(f"Dossier src: {SRC_DIR}")
    
    # Vérifier que le dossier src existe
    if not os.path.exists(SRC_DIR):
        print(f"ERREUR: Le dossier 'src' n'existe pas dans {CURRENT_DIR}")
        print(f"Contenu de {CURRENT_DIR}:")
        for item in os.listdir(CURRENT_DIR):
            print(f"  - {item}")
        raise FileNotFoundError(f"Dossier 'src' introuvable dans: {CURRENT_DIR}")
    
    # Vérifier le fichier main_window.py dans src
    main_window_file = os.path.join(SRC_DIR, "main_window.py")
    print(f"Recherche de: {main_window_file}")
    
    if not os.path.exists(main_window_file):
        print(f"\nERREUR: main_window.py non trouvé dans {SRC_DIR}")
        print(f"Contenu du dossier src:")
        for item in os.listdir(SRC_DIR):
            print(f"  - {item}")
        raise FileNotFoundError(f"Fichier main_window.py introuvable dans: {SRC_DIR}")
    
    # Ajouter le répertoire src au path Python
    if SRC_DIR not in sys.path:
        sys.path.insert(0, SRC_DIR)
    print(f"Python path mis à jour, SRC_DIR ajouté")
    
    try:
        # Importer PyQt6
        from PyQt6.QtWidgets import QApplication
        print("PyQt6 importé avec succès")
        
        # Importer main_window depuis le dossier src
        import main_window
        print("main_window importé avec succès")
        
        # Créer l'application Qt si nécessaire
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
            print("Application Qt créée")
        else:
            print("Application Qt déjà existante")
        
        # Créer l'instance de MainWindow
        window_instance = main_window.MainWindow()
        print("Instance MainWindow créée")
        
        return window_instance
        
    except ImportError as e:
        print(f"\nERREUR d'importation: {e}")
        print(f"Python path actuel: {sys.path}")
        print(f"Modules disponibles dans {SRC_DIR}:")
        for f in os.listdir(SRC_DIR):
            if f.endswith('.py'):
                print(f"  - {f}")
        raise
        
    except Exception as e:
        print(f"\nAUTRE ERREUR: {e}")
        import traceback
        traceback.print_exc()
        raise


# Pour exécution directe
if __name__ == "__main__":
    try:
        print("=" * 50)
        print("DÉMARRAGE DE L'APPLICATION")
        print("=" * 50)
        
        window = MainWindow()
        if window:
            print("\nAffichage de la fenêtre...")
            window.show()
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            if app:
                app.exec()
    except Exception as e:
        print(f"\nERREUR FATALE: {e}")
        import traceback
        traceback.print_exc()
        input("\nAppuyez sur Entrée pour quitter...")