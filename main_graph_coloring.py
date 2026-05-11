"""
Main FunSearch script for Graph Coloring heuristics evolution
"""

import os
import sys
import json
import time
import shutil
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import numpy as np

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from evaluation.evaluate_graph_coloring import evaluate_all_heuristics, save_evaluation_log
from funsearch_core.generator import FunSearchGenerator
from pathlib import Path


class FunSearchGraphColoring:
    """
    Main class for FunSearch Graph Coloring evolution
    """
    
    def __init__(self, max_cycles: int = 10, candidates_per_cycle: int = 5):
        """
        Initialize FunSearch for Graph Coloring.
        
        Args:
            max_cycles: Maximum number of evolution cycles
            candidates_per_cycle: Number of candidate heuristics to generate per cycle
        """
        self.max_cycles = max_cycles
        self.candidates_per_cycle = candidates_per_cycle
        
        # Directory structure
        self.base_dir = Path.cwd()
        self.heuristics_dir = self.base_dir / "heuristics"
        self.logs_dir = self.base_dir / "logs"
        self.graphs_dir = self.base_dir / "graphs"
        self.prompts_dir = self.base_dir / "prompts"
        self.benchmark_dir = self.base_dir / "graph_benchmark"
        
        # Ensure directories exist
        for directory in [self.heuristics_dir, self.logs_dir, self.graphs_dir]:
            directory.mkdir(exist_ok=True)
        
        # Evolution history
        self.evolution_history = []
        
        print(f"🎨 FunSearch Graph Coloring Initialisé")
        print(f"📊 Configuration: {max_cycles} cycles, {candidates_per_cycle} candidats/cycle")
    
    def create_baseline_heuristic(self) -> None:
        """Create a baseline greedy coloring heuristic"""
        baseline_code = '''
import networkx as nx
from typing import Dict

def color_graph(G: nx.Graph) -> Dict[int, int]:
    """
    Baseline greedy coloring - nodes in order of degree
    """
    if not G.nodes():
        return {}
    
    # Sort nodes by degree (highest first)
    nodes_by_degree = sorted(G.nodes(), key=lambda x: G.degree(x), reverse=True)
    
    coloring = {}
    used_colors = set()
    
    for node in nodes_by_degree:
        # Get colors used by neighbors
        neighbor_colors = set()
        for neighbor in G.neighbors(node):
            if neighbor in coloring:
                neighbor_colors.add(coloring[neighbor])
        
        # Assign the smallest available color
        color = 0
        while color in neighbor_colors:
            color += 1
        
        coloring[node] = color
        used_colors.add(color)
    
    return coloring

def get_heuristic_name() -> str:
    return "greedy_degree"

def get_heuristic_description() -> str:
    return "Greedy coloring - nodes processed in order of degree (highest first)"
'''
        
        baseline_file = self.heuristics_dir / "heuristic_0.py"
        with open(baseline_file, 'w') as f:
            f.write(baseline_code)
        
        print("✅ Heuristic de base créée: greedy_degree")
    
    def run_evolution(self) -> None:
        """Run the complete evolution process"""
        print("=" * 60)
        print("🚀 DÉMARRAGE DE L'ÉVOLUTION FUNSEARCH")
        print("=" * 60)
        
        # Create baseline if needed
        if not (self.heuristics_dir / "heuristic_0.py").exists():
            print("🔧 CRÉATION DE L'HEURISTIQUE DE BASE...")
            self.create_baseline_heuristic()
        
        # Run evolution cycles
        for cycle in range(1, self.max_cycles + 1):
            print(f"\n🔄 CYCLE {cycle}/{self.max_cycles}")
            print("-" * 40)
            
            # Evaluate current heuristics
            print("📏 ÉVALUATION DES HEURISTIQUES ACTUELLES...")
            results = evaluate_all_heuristics(
                str(self.heuristics_dir), 
                str(self.benchmark_dir),
                max_graphs=50  # Limit for faster evaluation
            )
            
            if not results:
                print("❌ Aucune heuristique valide trouvée")
                continue
            
            # Rank heuristics manually
            rankings = sorted(results, key=lambda x: x['enhanced_score'], reverse=True)
            
            # Get top heuristics manually
            top_heuristics = rankings[:3] if len(rankings) >= 3 else rankings
            
            # Save cycle results
            self._save_cycle_results(cycle, results, rankings)
            
            # Generate new heuristics
            print(f"🧪 GÉNÉRATION DE {self.candidates_per_cycle} NOUVELLE(S) HEURISTIQUE(S)...")
            self._generate_new_heuristics(rankings)
            
            # Update evolution history
            if rankings:
                best_score = rankings[0]['enhanced_score']
                avg_score = np.mean([r['enhanced_score'] for r in rankings])
                self.evolution_history.append({
                    'cycle': cycle,
                    'best_score': best_score,
                    'avg_score': avg_score,
                    'num_heuristics': len(rankings)
                })
                
                print(f"✅ Cycle {cycle} terminé - Meilleur score: {best_score:.2f}")
                print(f"📈 Nombre total d'heuristiques: {len(rankings)}")
            else:
                print(f"❌ Cycle {cycle} - Aucune heuristique valide")
        
        # Final evaluation and visualization
        print(f"\n🎯 ÉVALUATION FINALE ET GÉNÉRATION DES GRAPHIQUES...")
        self._generate_final_report()
        
        print("\n🎉 ÉVOLUTION TERMINÉE !")
        print(f"📊 Rapport final sauvegardé dans {self.logs_dir}/final_report.json")
        print(f"📈 Graphiques sauvegardés dans {self.graphs_dir}/evolution_summary.png")
    
    def _save_cycle_results(self, cycle: int, results: List[Dict], rankings: List[Dict]) -> None:
        """Save results for a specific cycle"""
        cycle_file = self.logs_dir / f"cycle_{cycle}.json"
        
        cycle_data = {
            'cycle': cycle,
            'timestamp': time.time(),
            'results': results,
            'rankings': rankings,
            'evolution_summary': {
                'cycle': cycle - 1,
                'best_score': self.evolution_history[-1]['best_score'] if self.evolution_history else 0,
                'num_heuristics': len(rankings),
                'avg_score': np.mean([r['enhanced_score'] for r in rankings]) if rankings else 0
            }
        }
        
        with open(cycle_file, 'w') as f:
            json.dump(cycle_data, f, indent=2)
        
        print(f"💾 Sauvegarde des résultats du cycle {cycle}")
    
    def _generate_new_heuristics(self, rankings: List[Dict]) -> None:
        """Generate new heuristics using the top performers"""
        if not rankings:
            print("❌ Aucune heuristique disponible pour la génération")
            return
        
        # Get top heuristics
        top_heuristics = rankings[:3] if len(rankings) >= 3 else rankings
        heuristic_codes = []
        
        print("📋 Analyse des meilleures heuristiques...")
        for i, heuristic in enumerate(top_heuristics):
            print(f"  ✅ Heuristic {i+1}: {heuristic['heuristic_file']}")
            
            # Load heuristic code
            heuristic_file = self.heuristics_dir / heuristic['heuristic_file']
            with open(heuristic_file, 'r') as f:
                code = f.read()
                heuristic_codes.append(code)
        
        # Create generator
        prompt_template_file = self.prompts_dir / "llm_prompt_graph_coloring.txt"
        print("🤖 Initialisation du générateur LLM...")
        generator = FunSearchGenerator(Path(prompt_template_file))
        
        # Generate new heuristics
        print(f"🧠 Génération de {self.candidates_per_cycle} nouvelle(s) heuristique(s) via LLM...")
        new_heuristics = generator.generate_candidates(
            previous_solutions=heuristic_codes, 
            n=self.candidates_per_cycle
        )
        
        # Save new heuristics
        current_cycle = len(self.evolution_history) + 1
        print(f"💾 Sauvegarde des heuristiques du cycle {current_cycle}...")
        
        for i, heuristic_code in enumerate(new_heuristics):
            try:
                heuristic_name = generator.save_heuristic_to_collection(
                    heuristic_code, current_cycle, i+1
                )
                print(f"  ✅ Heuristic générée: {heuristic_name}")
            except Exception as e:
                print(f"  ❌ Erreur génération heuristique {i+1}: {e}")
        
        print(f"🎉 Génération terminée: {len(new_heuristics)} heuristiques créées")
    
    def _generate_final_report(self) -> None:
        """Generate final report and visualizations"""
        if not self.evolution_history:
            print("❌ Aucune donnée d'évolution à analyser")
            return
        
        # Create evolution plots
        self._create_evolution_plots()
        
        # Save final report
        final_report = {
            'experiment_summary': {
                'total_cycles': len(self.evolution_history),
                'max_cycles': self.max_cycles,
                'candidates_per_cycle': self.candidates_per_cycle,
                'start_time': 1,
                'end_time': len(self.evolution_history)
            },
            'evolution_history': self.evolution_history,
            'final_best_score': self.evolution_history[-1]['best_score'] if self.evolution_history else 0,
            'improvement': (self.evolution_history[-1]['best_score'] - self.evolution_history[0]['best_score']) if len(self.evolution_history) > 1 else 0
        }
        
        report_file = self.logs_dir / "final_report.json"
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2)
    
    def _create_evolution_plots(self) -> None:
        """Create visualization plots for evolution"""
        if not self.evolution_history:
            return
        
        cycles = [h['cycle'] for h in self.evolution_history]
        best_scores = [h['best_score'] for h in self.evolution_history]
        avg_scores = [h['avg_score'] for h in self.evolution_history]
        num_heuristics = [h['num_heuristics'] for h in self.evolution_history]
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        
        # Best scores over time
        ax1.plot(cycles, best_scores, 'b-', linewidth=2, marker='o')
        ax1.set_title('Évolution du Meilleur Score')
        ax1.set_xlabel('Cycle')
        ax1.set_ylabel('Score')
        ax1.grid(True, alpha=0.3)
        
        # Average scores over time
        ax2.plot(cycles, avg_scores, 'g-', linewidth=2, marker='s')
        ax2.set_title('Évolution du Score Moyen')
        ax2.set_xlabel('Cycle')
        ax2.set_ylabel('Score')
        ax2.grid(True, alpha=0.3)
        
        # Number of heuristics
        ax3.bar(cycles, num_heuristics, alpha=0.7, color='purple')
        ax3.set_title('Nombre d\'Heuristiques par Cycle')
        ax3.set_xlabel('Cycle')
        ax3.set_ylabel('Nombre')
        ax3.grid(True, alpha=0.3)
        
        # Score distribution
        all_scores = []
        for h in self.evolution_history:
            all_scores.extend([h['best_score'], h['avg_score']])
        
        ax4.hist(all_scores, bins=20, alpha=0.7, color='orange', edgecolor='black')
        ax4.set_title('Distribution des Scores')
        ax4.set_xlabel('Score')
        ax4.set_ylabel('Fréquence')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plot_file = self.graphs_dir / "evolution_summary.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📈 Graphiques sauvegardés dans {plot_file}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="FunSearch Graph Coloring Evolution")
    parser.add_argument("--cycles", type=int, default=10, help="Number of evolution cycles")
    parser.add_argument("--candidates", type=int, default=5, help="Candidates per cycle")
    
    args = parser.parse_args()
    
    # Run FunSearch
    funsearch = FunSearchGraphColoring(max_cycles=args.cycles, candidates_per_cycle=args.candidates)
    funsearch.run_evolution()


if __name__ == "__main__":
    main()
