"""
Main FunSearch script for Graph Coloring heuristics evolution - OPTIMIZED VERSION

Configuration optimisée pour étude académique robuste:
- 12 cycles d'évolution
- 5 candidats par cycle  
- 100 graphes benchmark
- 60 heuristiques totales générées
"""

import os
import sys
import json
import time
import shutil
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from evaluation.evaluate_graph_coloring import evaluate_all_heuristics, save_evaluation_log
from funsearch_core.generator_api_fixed import FunSearchAPIGeneratorFixed
import sys
sys.path.append('funsearch_core')
from api_client import LLMAPIClient


class FunSearchGraphColoringOptimized:
    """
    Version optimisée pour étude académique robuste de FunSearch Graph Coloring
    """
    
    def __init__(self, max_cycles: int = 12, candidates_per_cycle: int = 5, 
                 provider: str = "mistral", api_key: str = None, max_graphs: int = 100):
        """
        Initialize FunSearch optimisé pour étude académique.
        
        Args:
            max_cycles: 12 cycles pour convergence complète
            candidates_per_cycle: 5 candidats pour diversité suffisante
            provider: LLM provider ("mistral", "openai", "claude")
            api_key: API key (optional)
            max_graphs: 100 graphes pour évaluation statistique
        """
        self.max_cycles = max_cycles
        self.candidates_per_cycle = candidates_per_cycle
        self.provider = provider
        self.max_graphs = max_graphs
        
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
        self.all_generated_heuristics = []
        
        print(f"🎨 FunSearch Graph Coloring Optimisé Initialisé")
        print(f"📊 Configuration: {max_cycles} cycles, {candidates_per_cycle} candidats/cycle")
        print(f"📈 Total attendu: {max_cycles * candidates_per_cycle} heuristiques")
        print(f"🧪 Benchmark: {max_graphs} graphes")
        print(f"🤖 Provider: {provider.upper()}")
        print(f"💰 Coût estimé: ~${(max_cycles * candidates_per_cycle * 0.025):.2f}")
    
    def create_baseline_heuristic(self) -> None:
        """Create baseline greedy coloring heuristic"""
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
        
        # Assign smallest available color
        color = 0
        while color in neighbor_colors:
            color += 1
        
        coloring[node] = color
        used_colors.add(color)
    
    return coloring

def get_heuristic_name() -> str:
    return "greedy_degree_baseline"

def get_heuristic_description() -> str:
    return "Baseline greedy coloring - nodes processed in order of degree (highest first)"
'''
        
        baseline_file = self.heuristics_dir / "heuristic_0.py"
        with open(baseline_file, 'w') as f:
            f.write(baseline_code)
        
        print("✅ Heuristic de base créée: greedy_degree_baseline")
    
    def run_evolution(self) -> None:
        """Run complete optimized evolution process"""
        print("=" * 80)
        print("🚀 DÉMARRAGE DE L'ÉVOLUTION FUNSEARCH OPTIMISÉ")
        print("=" * 80)
        print(f"📊 Objectif: {self.max_cycles} cycles × {self.candidates_per_cycle} candidats = {self.max_cycles * self.candidates_per_cycle} heuristiques")
        print(f"🧪 Évaluation sur {self.max_graphs} graphes benchmark")
        print("=" * 80)
        
        # Create baseline if needed
        if not (self.heuristics_dir / "heuristic_0.py").exists():
            print("🔧 CRÉATION DE L'HEURISTIQUE DE BASE...")
            self.create_baseline_heuristic()
        
        # Initialize API generator
        try:
            prompt_template_file = self.prompts_dir / "llm_prompt_graph_coloring.txt"
            generator = FunSearchAPIGeneratorFixed(prompt_template_file, self.provider)
        except Exception as e:
            print(f"❌ Erreur initialisation API: {e}")
            print("Vérifiez votre clé API:")
            print(f"export {self.provider.upper()}_API_KEY='votre_clé'")
            return
        
        # Run evolution cycles
        start_time = time.time()
        
        for cycle in range(1, self.max_cycles + 1):
            print(f"\n🔄 CYCLE {cycle}/{self.max_cycles}")
            print("-" * 60)
            
            # Evaluate current heuristics
            print("📏 ÉVALUATION DES HEURISTIQUES ACTUELLES...")
            results = evaluate_all_heuristics(
                str(self.heuristics_dir), 
                str(self.benchmark_dir),
                max_graphs=self.max_graphs
            )
            
            if not results:
                print("❌ Aucune heuristique valide trouvée")
                continue
            
            # Rank heuristics
            rankings = sorted(results, key=lambda x: x['enhanced_score'], reverse=True)
            
            # Save cycle results
            self._save_cycle_results(cycle, results, rankings)
            
            # Generate new heuristics
            print(f"🧪 GÉNÉRATION DE {self.candidates_per_cycle} NOUVELLE(S) HEURISTIQUE(S)...")
            self._generate_new_heuristics(rankings, generator)
            
            # Update evolution history
            if rankings:
                best_score = rankings[0]['enhanced_score']
                avg_score = np.mean([r['enhanced_score'] for r in rankings])
                
                evolution_entry = {
                    'cycle': cycle,
                    'best_score': best_score,
                    'avg_score': avg_score,
                    'num_heuristics': len(rankings),
                    'best_heuristic': rankings[0]['heuristic_file'],
                    'baseline_score': next((r['enhanced_score'] for r in rankings if r['heuristic_file'] == 'heuristic_0.py'), None)
                }
                
                self.evolution_history.append(evolution_entry)
                
                # Calculate improvement
                if cycle == 1:
                    baseline_score = evolution_entry['baseline_score']
                    print(f"✅ Cycle {cycle} terminé")
                    print(f"   🏆 Meilleur score: {best_score:.2f}")
                    print(f"   📊 Baseline: {baseline_score:.2f}")
                    print(f"   📈 Nombre total: {len(rankings)} heuristiques")
                else:
                    improvement = best_score - self.evolution_history[0]['baseline_score']
                    print(f"✅ Cycle {cycle} terminé")
                    print(f"   🏆 Meilleur score: {best_score:.2f}")
                    print(f"   📈 Amélioration vs baseline: {improvement:+.2f}")
                    print(f"   📊 Nombre total: {len(rankings)} heuristiques")
            else:
                print(f"❌ Cycle {cycle} - Aucune heuristique valide")
        
        total_time = time.time() - start_time
        
        # Final evaluation and visualization
        print(f"\n🎯 ÉVALUATION FINALE ET GÉNÉRATION DES GRAPHIQUES...")
        self._generate_final_report()
        
        print(f"\n🎉 ÉVOLUTION TERMINÉE !")
        print(f"⏱️  Temps total: {total_time:.1f} secondes")
        print(f"📊 Rapport final: {self.logs_dir}/final_report_optimized.json")
        print(f"📈 Graphiques: {self.graphs_dir}/evolution_optimized.png")
        print(f"🧪 Total heuristiques générées: {len(self.all_generated_heuristics)}")
    
    def _save_cycle_results(self, cycle: int, results: List[Dict], rankings: List[Dict]) -> None:
        """Save detailed results for each cycle"""
        cycle_file = self.logs_dir / f"cycle_{cycle:02d}_optimized.json"
        
        cycle_data = {
            'cycle': cycle,
            'provider': self.provider,
            'timestamp': time.time(),
            'benchmark_size': self.max_graphs,
            'results': results,
            'rankings': rankings,
            'summary': {
                'cycle': cycle,
                'total_heuristics': len(rankings),
                'best_score': rankings[0]['enhanced_score'] if rankings else 0,
                'avg_score': np.mean([r['enhanced_score'] for r in rankings]) if rankings else 0,
                'baseline_score': next((r['enhanced_score'] for r in rankings if r['heuristic_file'] == 'heuristic_0.py'), 0),
                'improvement': 0
            }
        }
        
        # Calculate improvement
        baseline_score = cycle_data['summary']['baseline_score']
        if baseline_score > 0:
            cycle_data['summary']['improvement'] = (cycle_data['summary']['best_score'] - baseline_score) / baseline_score * 100
        
        with open(cycle_file, 'w') as f:
            json.dump(cycle_data, f, indent=2)
        
        print(f"💾 Résultats du cycle {cycle} sauvegardés")
    
    def _generate_new_heuristics(self, rankings: List[Dict], generator: FunSearchAPIGeneratorFixed) -> None:
        """Generate new heuristics using top performers"""
        if not rankings:
            print("❌ Aucune heuristique disponible pour la génération")
            return
        
        # Get top 3 heuristics
        top_heuristics = rankings[:3] if len(rankings) >= 3 else rankings
        heuristic_codes = []
        
        print("📋 Analyse des meilleures heuristiques...")
        for i, heuristic in enumerate(top_heuristics):
            print(f"  ✅ Top {i+1}: {heuristic['heuristic_file']} (score: {heuristic['enhanced_score']:.2f})")
            
            # Load heuristic code
            heuristic_file = self.heuristics_dir / heuristic['heuristic_file']
            with open(heuristic_file, 'r') as f:
                code = f.read()
                heuristic_codes.append(code)
        
        # Generate new heuristics
        print(f"🧠 Génération via API {self.provider.upper()}...")
        new_heuristics = generator.generate_candidates(
            previous_solutions=heuristic_codes, 
            n=self.candidates_per_cycle
        )
        
        # Save new heuristics
        current_cycle = len(self.evolution_history) + 1
        print(f"💾 Sauvegarde des {len(new_heuristics)} heuristiques du cycle {current_cycle}...")
        
        for i, heuristic_code in enumerate(new_heuristics):
            try:
                heuristic_name = generator.save_heuristic_to_collection(
                    heuristic_code, current_cycle, i+1
                )
                self.all_generated_heuristics.append({
                    'name': heuristic_name,
                    'cycle': current_cycle,
                    'candidate': i+1,
                    'code_length': len(heuristic_code)
                })
                print(f"  ✅ {heuristic_name}")
            except Exception as e:
                print(f"  ❌ Erreur sauvegarde candidat {i+1}: {e}")
        
        print(f"🎉 Génération terminée: {len(new_heuristics)}/{self.candidates_per_cycle} heuristiques créées")
    
    def _generate_final_report(self) -> None:
        """Generate comprehensive final report and visualizations"""
        if not self.evolution_history:
            print("❌ Aucune donnée d'évolution à analyser")
            return
        
        # Create detailed evolution plots
        self._create_comprehensive_plots()
        
        # Calculate final statistics
        final_report = {
            'experiment_summary': {
                'total_cycles': len(self.evolution_history),
                'max_cycles': self.max_cycles,
                'candidates_per_cycle': self.candidates_per_cycle,
                'provider': self.provider,
                'benchmark_size': self.max_graphs,
                'total_heuristics_generated': len(self.all_generated_heuristics),
                'start_time': 1,
                'end_time': len(self.evolution_history)
            },
            'evolution_history': self.evolution_history,
            'final_statistics': self._calculate_final_statistics(),
            'generated_heuristics': self.all_generated_heuristics,
            'conclusions': self._generate_conclusions()
        }
        
        report_file = self.logs_dir / "final_report_optimized.json"
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2)
    
    def _calculate_final_statistics(self) -> Dict[str, Any]:
        """Calculate comprehensive statistics"""
        if not self.evolution_history:
            return {}
        
        scores = [h['best_score'] for h in self.evolution_history]
        baseline_score = self.evolution_history[0]['baseline_score']
        
        return {
            'baseline_score': baseline_score,
            'final_best_score': scores[-1],
            'max_score': max(scores),
            'min_score': min(scores),
            'avg_score': np.mean(scores),
            'improvement_absolute': scores[-1] - baseline_score,
            'improvement_percentage': ((scores[-1] - baseline_score) / baseline_score * 100) if baseline_score != 0 else 0,
            'score_std': np.std(scores),
            'convergence_cycle': next((i+1 for i, s in enumerate(scores) if s >= max(scores) * 0.95), len(scores))
        }
    
    def _generate_conclusions(self) -> List[str]:
        """Generate automated conclusions"""
        stats = self._calculate_final_statistics()
        conclusions = []
        
        if stats.get('improvement_percentage', 0) > 5:
            conclusions.append(f"✅ Succès significatif: +{stats['improvement_percentage']:.1f}% vs baseline")
        elif stats.get('improvement_percentage', 0) > 0:
            conclusions.append(f"📈 Amélioration modeste: +{stats['improvement_percentage']:.1f}% vs baseline")
        else:
            conclusions.append("❌ Aucune amélioration détectée vs baseline")
        
        if stats.get('convergence_cycle', 0) < len(self.evolution_history) // 2:
            conclusions.append(f"⚡ Convergence rapide: cycle {stats['convergence_cycle']}")
        else:
            conclusions.append(f"🐌 Convergence lente: cycle {stats['convergence_cycle']}")
        
        success_rate = len(self.all_generated_heuristics) / (self.max_cycles * self.candidates_per_cycle) * 100
        if success_rate > 80:
            conclusions.append(f"🎯 Taux de succès élevé: {success_rate:.1f}%")
        else:
            conclusions.append(f"⚠️  Taux de succès modéré: {success_rate:.1f}%")
        
        return conclusions
    
    def _create_comprehensive_plots(self) -> None:
        """Create detailed visualization plots"""
        if not self.evolution_history:
            return
        
        cycles = [h['cycle'] for h in self.evolution_history]
        best_scores = [h['best_score'] for h in self.evolution_history]
        avg_scores = [h['avg_score'] for h in self.evolution_history]
        num_heuristics = [h['num_heuristics'] for h in self.evolution_history]
        baseline_scores = [h['baseline_score'] for h in self.evolution_history]
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Best scores evolution with baseline
        ax1.plot(cycles, best_scores, 'b-', linewidth=3, marker='o', markersize=6, label='Meilleur score')
        ax1.axhline(y=baseline_scores[0], color='r', linestyle='--', alpha=0.7, label='Baseline')
        ax1.set_title(f'Évolution du Meilleur Score ({self.provider.upper()})', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Cycle', fontsize=12)
        ax1.set_ylabel('Score', fontsize=12)
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # Average scores
        ax2.plot(cycles, avg_scores, 'g-', linewidth=3, marker='s', markersize=6, color='green')
        ax2.set_title(f'Évolution du Score Moyen ({self.provider.upper()})', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Cycle', fontsize=12)
        ax2.set_ylabel('Score Moyen', fontsize=12)
        ax2.grid(True, alpha=0.3)
        
        # Number of heuristics per cycle
        ax3.bar(cycles, num_heuristics, alpha=0.8, color='purple')
        ax3.set_title('Nombre d\'Heuristiques Valides par Cycle', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Cycle', fontsize=12)
        ax3.set_ylabel('Nombre', fontsize=12)
        ax3.grid(True, alpha=0.3)
        
        # Score distribution and improvement
        all_scores = best_scores + avg_scores
        ax4.hist(all_scores, bins=20, alpha=0.7, color='orange', edgecolor='black')
        ax4.axvline(x=baseline_scores[0], color='r', linestyle='--', linewidth=2, label='Baseline')
        ax4.set_title('Distribution des Scores', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Score', fontsize=12)
        ax4.set_ylabel('Fréquence', fontsize=12)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plot_file = self.graphs_dir / "evolution_optimized.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📈 Graphiques détaillés sauvegardés: {plot_file}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="FunSearch Graph Coloring Evolution - Optimized")
    parser.add_argument("--cycles", type=int, default=12, help="Number of evolution cycles (default: 12)")
    parser.add_argument("--candidates", type=int, default=5, help="Candidates per cycle (default: 5)")
    parser.add_argument("--graphs", type=int, default=100, help="Benchmark graphs (default: 100)")
    parser.add_argument("--provider", type=str, default="mistral", 
                       choices=["mistral", "openai", "claude"], help="LLM provider")
    
    args = parser.parse_args()
    
    # Run optimized FunSearch
    funsearch = FunSearchGraphColoringOptimized(
        max_cycles=args.cycles, 
        candidates_per_cycle=args.candidates,
        max_graphs=args.graphs,
        provider=args.provider
    )
    funsearch.run_evolution()


if __name__ == "__main__":
    main()
