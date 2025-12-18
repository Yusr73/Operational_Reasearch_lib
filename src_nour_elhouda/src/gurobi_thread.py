# src/gurobi_thread.py
"""
Thread dédié à l'exécution du solveur Gurobi pour éviter le blocage de l'interface.
"""

from PyQt6.QtCore import QThread, pyqtSignal
from gurobi_solver import MinCostFlowSolver
import traceback

class GurobiThread(QThread):
    """Thread pour exécuter Gurobi sans bloquer l'interface"""
    
    # Signaux pour communiquer avec l'interface
    solution_ready = pyqtSignal(dict)
    error_occurred = pyqtSignal(str)
    progress_updated = pyqtSignal(int)
    
    def __init__(self, network_data, supply_demand, options=None):
        super().__init__()
        self.network_data = network_data
        self.supply_demand = supply_demand
        self.options = options or {}
        self.solver = MinCostFlowSolver()
    
    def run(self):
        """Méthode exécutée dans le thread"""
        try:
            # Vérifier les données
            if not self.network_data or not self.supply_demand:
                raise ValueError("Données manquantes")
            
            # Vérifier la structure des données
            if 'nodes' not in self.network_data or 'arcs' not in self.network_data:
                raise ValueError("Structure de données réseau invalide")
            
            # Vérifier que les arcs ont les bonnes clés
            for i, arc in enumerate(self.network_data.get('arcs', [])):
                required_keys = ['source', 'destination', 'cost', 'capacity']
                for key in required_keys:
                    if key not in arc:
                        raise ValueError(f"Arc {i+1} manquant de la clé: {key}")
                
                # Vérifier les types
                try:
                    float(arc['cost'])
                    float(arc['capacity'])
                except ValueError:
                    raise ValueError(f"Arc {i+1}: coût ou capacité invalide")
            
            # Vérifier l'équilibre offre/demande
            total_supply = sum(v for v in self.supply_demand.values() if v > 0)
            total_demand = abs(sum(v for v in self.supply_demand.values() if v < 0))
            
            print(f"\n[Thread] Vérification données:")
            print(f"  Nœuds: {len(self.network_data['nodes'])}")
            print(f"  Arcs: {len(self.network_data['arcs'])}")
            print(f"  Offre totale: {total_supply:,.0f}")
            print(f"  Demande totale: {total_demand:,.0f}")
            
            if total_supply == 0 and total_demand == 0:
                print("  ⚠️ Avertissement: Offre et demande totales sont nulles")
            
            # Émettre le début de la résolution
            self.progress_updated.emit(10)
            
            # Résoudre le problème avec la version corrigée
            results = self.solver.solve_with_fallback(
                self.network_data, 
                self.supply_demand, 
                self.options
            )
            
            # Émettre la progression
            self.progress_updated.emit(90)
            
            # Ajouter des informations supplémentaires
            results['network_summary'] = {
                'num_nodes': len(self.network_data['nodes']),
                'num_arcs': len(self.network_data['arcs']),
                'total_supply': total_supply,
                'total_demand': total_demand,
                'balance_diff': total_supply - total_demand
            }
            
            # Émettre les résultats
            self.progress_updated.emit(100)
            self.solution_ready.emit(results)
            
            print(f"[Thread] Résolution terminée - Statut: {results.get('status', 'N/A')}")
            
        except Exception as e:
            # Capturer et émettre l'erreur
            error_msg = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
            print(f"[Thread] ERREUR: {error_msg}")
            self.error_occurred.emit(error_msg)