"""
Main FunSearch Script - VERSION ROBUSTE

Script principal pour étude académique robuste avec générateur corrigé
"""

import os
import sys
import json
import time
from typing import List, Dict, Any
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Add paths
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append('funsearch_core')

from evaluation.evaluate_graph_coloring import evaluate_all_heuristics
from funsearch_core.generator_robust import RobustFunSearchGenerator


class RobustFunSearchMain:
    """
    Version robuste pour étude académique FunSearch
    """
    
    def __init__(self, max_cycles: int = 8, candidates_per_cycle: int = 4, 
                 provider: str = "mistral", max_graphs: int = 75):
        """
        Initialisation robuste
        
        Args:
            max_cycles: 8 cycles pour étude équilibrée
            candidates_per_cycle: 4 candidats pour diversité
            provider: LLM provider
            max_graphs: 75 graphes pour évaluation statistique
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
        self.successful_generations = 0
        
        print(f"🎨 FunSearch Robuste Initialisé")
        print(f"📊 Configuration: {max_cycles} cycles, {candidates_per_cycle} candidats/cycle")
        print(f"🧪 Benchmark: {max_graphs} graphes")
        print(f"🤖 Provider: {provider.upper()}")
        print(f"🎯 Objectif: {max_cycles * candidates_per_cycle} heuristiques totales")
    
    def run_evolution(self) -> None:
        """Lancer l'évolution robuste"""
        print("=" * 80)
        print("🚀 DÉMARRAGE FUNSEARCH ROBUSTE")
        print("=" * 80)
        
        # Initialize generator
        try:
            prompt_file = self.prompts_dir / "llm_prompt_graph_coloring.txt"
            generator = RobustFunSearchGenerator(prompt_file, self.provider)
        except Exception as e:
            print(f"❌ Erreur initialisation: {e}")
            return
        
        # Run cycles
        start_time = time.time()
        
        for cycle in range(1, self.max_cycles + 1):
            print(f"\n🔄 CYCLE {cycle}/{self.max_cycles}")
            print("-" * 60)
            
            # Evaluate current heuristics
            print("📏 Évaluation des heuristiques...")
            results = self._evaluate_current_heuristics()
            
            if not results:
                print("❌ Aucune heuristique valide trouvée")
                continue
            
            # Rank and save
            rankings = sorted(results, key=lambda x: x['enhanced_score'], reverse=True)
            self._save_cycle_results(cycle, results, rankings)
            
            # Generate new heuristics
            print(f"🧪 Génération de {self.candidates_per_cycle} nouvelles heuristiques...")
            new_count = self._generate_new_heuristics(rankings, generator)
            self.successful_generations += new_count
            
            # Update history
            if rankings:
                best_score = rankings[0]['enhanced_score']
                avg_score = np.mean([r['enhanced_score'] for r in rankings])
                
                evolution_entry = {
                    'cycle': cycle,
                    'best_score': best_score,
                    'avg_score': avg_score,
                    'num_heuristics': len(rankings),
                    'new_generated': new_count,
                    'success_rate': (new_count / self.candidates_per_cycle) * 100
                }
                
                self.evolution_history.append(evolution_entry)
                
                print(f"✅ Cycle {cycle} terminé")
                print(f"   🏆 Meilleur score: {best_score:.2f}")
                print(f"   📊 Heuristiques: {len(rankings)}")
                print(f"   🎯 Générées: {new_count}/{self.candidates_per_cycle} ({evolution_entry['success_rate']:.0f}%)")
        
        total_time = time.time() - start_time
        
        # Final report
        self._generate_final_report()
        
        print(f"\n🎉 ÉVOLUTION TERMINÉE !")
        print(f"⏱️  Temps total: {total_time:.1f}s")
        print(f"🧪 Générées: {self.successful_generations}/{self.max_cycles * self.candidates_per_cycle}")
        print(f"📊 Succès: {(self.successful_generations/(self.max_cycles * self.candidates_per_cycle)*100):.1f}%")
        print(f"📈 Rapport: {self.logs_dir}/robust_final_report.json")
    
    def _evaluate_current_heuristics(self) -> List[Dict]:
        """Évaluer les heuristiques actuelles"""
        try:
            results = evaluate_all_heuristics(
                str(self.heuristics_dir), 
                str(self.benchmark_dir),
                max_graphs=self.max_graphs
            )
            return results
        except Exception as e:
            print(f"❌ Erreur évaluation: {e}")
            return []
    
    def _save_cycle_results(self, cycle: int, results: List[Dict], rankings: List[Dict]) -> None:
        """Sauvegarder résultats du cycle"""
        cycle_file = self.logs_dir / f"robust_cycle_{cycle:02d}.json"
        
        cycle_data = {
            'cycle': cycle,
            'timestamp': time.time(),
            'provider': self.provider,
            'benchmark_size': self.max_graphs,
            'results': results,
            'rankings': rankings,
            'summary': {
                'total_heuristics': len(rankings),
                'best_score': rankings[0]['enhanced_score'] if rankings else 0,
                'avg_score': np.mean([r['enhanced_score'] for r in rankings]) if rankings else 0
            }
        }
        
        with open(cycle_file, 'w') as f:
            json.dump(cycle_data, f, indent=2)
    
    def _generate_new_heuristics(self, rankings: List[Dict], generator: RobustFunSearchGenerator) -> int:
        """Générer nouvelles heuristiques"""
        if not rankings:
            return 0
        
        # Get top heuristics for inspiration
        top_heuristics = rankings[:2] if len(rankings) >= 2 else rankings
        heuristic_codes = []
        
        print("📋 Analyse des meilleures heuristiques...")
        for i, h in enumerate(top_heuristics):
            print(f"  ✅ Top {i+1}: {h['heuristic_file']} (score: {h['enhanced_score']:.2f})")
            
            try:
                heuristic_file = self.heuristics_dir / h['heuristic_file']
                with open(heuristic_file, 'r') as f:
                    code = f.read()
                    heuristic_codes.append(code)
            except:
                continue
        
        # Generate new candidates
        try:
            new_heuristics = generator.generate_candidates(
                previous_solutions=heuristic_codes,
                n=self.candidates_per_cycle
            )
            
            # Save generated heuristics
            for i, code in enumerate(new_heuristics):
                try:
                    generator.save_heuristic(code, len(self.evolution_history) + 1, i + 1)
                except Exception as e:
                    print(f"  ❌ Erreur sauvegarde {i+1}: {e}")
            
            return len(new_heuristics)
            
        except Exception as e:
            print(f"❌ Erreur génération: {e}")
            return 0
    
    def _generate_final_report(self) -> None:
        """Générer rapport final"""
        if not self.evolution_history:
            return
        
        # Statistics
        total_targets = self.max_cycles * self.candidates_per_cycle
        success_rate = (self.successful_generations / total_targets) * 100
        
        final_report = {
            'experiment_summary': {
                'total_cycles': len(self.evolution_history),
                'max_cycles': self.max_cycles,
                'candidates_per_cycle': self.candidates_per_cycle,
                'provider': self.provider,
                'benchmark_size': self.max_graphs,
                'total_targets': total_targets,
                'successful_generations': self.successful_generations,
                'success_rate': success_rate
            },
            'evolution_history': self.evolution_history,
            'final_statistics': {
                'avg_success_rate': np.mean([h['success_rate'] for h in self.evolution_history]),
                'best_cycle_score': max([h['best_score'] for h in self.evolution_history]),
                'improvement': self._calculate_improvement(),
                'convergence_analysis': self._analyze_convergence()
            },
            'conclusions': self._generate_conclusions(success_rate)
        }
        
        # Save report
        report_file = self.logs_dir / "robust_final_report.json"
        with open(report_file, 'w') as f:
            json.dump(final_report, f, indent=2)
        
        # Create plots
        self._create_plots()
    
    def _calculate_improvement(self) -> Dict[str, float]:
        """Calculer l'amélioration"""
        if len(self.evolution_history) < 2:
            return {'improvement': 0.0, 'percentage': 0.0}
        
        first_score = self.evolution_history[0]['best_score']
        last_score = self.evolution_history[-1]['best_score']
        
        improvement = last_score - first_score
        percentage = (improvement / first_score * 100) if first_score != 0 else 0
        
        return {'improvement': improvement, 'percentage': percentage}
    
    def _analyze_convergence(self) -> Dict[str, Any]:
        """Analyser la convergence"""
        if not self.evolution_history:
            return {}
        
        scores = [h['best_score'] for h in self.evolution_history]
        max_score = max(scores)
        
        # Cycle où on atteint 95% du max
        convergence_cycle = next((i+1 for i, s in enumerate(scores) if s >= max_score * 0.95), len(scores))
        
        return {
            'max_score': max_score,
            'convergence_cycle': convergence_cycle,
            'early_convergence': convergence_cycle <= len(scores) // 2
        }
    
    def _generate_conclusions(self, success_rate: float) -> List[str]:
        """Générer conclusions automatiques"""
        conclusions = []
        
        if success_rate >= 80:
            conclusions.append(f"✅ Excellent taux de succès: {success_rate:.1f}%")
        elif success_rate >= 50:
            conclusions.append(f"📊 Bon taux de succès: {success_rate:.1f}%")
        else:
            conclusions.append(f"⚠️  Taux de succès faible: {success_rate:.1f}%")
        
        improvement = self._calculate_improvement()
        if improvement['percentage'] > 5:
            conclusions.append(f"🚀 Amélioration significative: +{improvement['percentage']:.1f}%")
        elif improvement['percentage'] > 0:
            conclusions.append(f"📈 Amélioration modeste: +{improvement['percentage']:.1f}%")
        else:
            conclusions.append("➡️  Aucune amélioration détectée")
        
        return conclusions
    
    def _create_plots(self) -> None:
        """Créer graphiques"""
        if not self.evolution_history:
            return
        
        cycles = [h['cycle'] for h in self.evolution_history]
        best_scores = [h['best_score'] for h in self.evolution_history]
        success_rates = [h['success_rate'] for h in self.evolution_history]
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
        
        # Best scores
        ax1.plot(cycles, best_scores, 'b-', linewidth=3, marker='o', markersize=6)
        ax1.set_title('Évolution du Meilleur Score', fontsize=14, fontweight='bold')
        ax1.set_xlabel('Cycle')
        ax1.set_ylabel('Score')
        ax1.grid(True, alpha=0.3)
        
        # Success rates
        ax2.bar(cycles, success_rates, alpha=0.8, color='green')
        ax2.set_title('Taux de Succès par Cycle', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Cycle')
        ax2.set_ylabel('Succès (%)')
        ax2.grid(True, alpha=0.3)
        
        # Score distribution
        ax3.hist(best_scores, bins=15, alpha=0.7, color='orange', edgecolor='black')
        ax3.set_title('Distribution des Scores', fontsize=14, fontweight='bold')
        ax3.set_xlabel('Score')
        ax3.set_ylabel('Fréquence')
        ax3.grid(True, alpha=0.3)
        
        # Cumulative success
        cumulative_success = np.cumsum([h['new_generated'] for h in self.evolution_history])
        ax4.plot(cycles, cumulative_success, 'purple', linewidth=3, marker='s', markersize=6)
        ax4.set_title('Heuristiques Cumulées Générées', fontsize=14, fontweight='bold')
        ax4.set_xlabel('Cycle')
        ax4.set_ylabel('Total')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plot_file = self.graphs_dir / "robust_evolution.png"
        plt.savefig(plot_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📈 Graphiques sauvegardés: {plot_file}")


def main():
    """Point d'entrée principal"""
    import argparse
    
    parser = argparse.ArgumentParser(description="FunSearch Robust - Graph Coloring")
    parser.add_argument("--cycles", type=int, default=8, help="Nombre de cycles")
    parser.add_argument("--candidates", type=int, default=4, help="Candidats par cycle")
    parser.add_argument("--graphs", type=int, default=75, help="Graphes benchmark")
    parser.add_argument("--provider", type=str, default="mistral", 
                       choices=["mistral", "openai", "claude"], help="LLM provider")
    
    args = parser.parse_args()
    
    # Lancer FunSearch robuste
    funsearch = RobustFunSearchMain(
        max_cycles=args.cycles,
        candidates_per_cycle=args.candidates,
        max_graphs=args.graphs,
        provider=args.provider
    )
    funsearch.run_evolution()


if __name__ == "__main__":
    main()
