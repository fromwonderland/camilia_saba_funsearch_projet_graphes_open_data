"""
Evaluation module for graph coloring heuristics
"""

import time
import json
import networkx as nx
import numpy as np
from typing import Dict, List, Any, Tuple
import os
import importlib.util

def load_graph_from_json(filename: str) -> nx.Graph:
    """Load a graph from JSON file"""
    with open(filename, 'r') as f:
        data = json.load(f)
    
    G = nx.Graph()
    G.add_nodes_from(data['nodes'])
    G.add_edges_from(data['edges'])
    G.name = data['name']
    
    return G

def load_benchmark(benchmark_dir: str = "graph_benchmark", max_graphs: int = 100) -> List[nx.Graph]:
    """Load benchmark graphs"""
    graphs = []
    
    try:
        # Load all graph files
        graph_files = [f for f in os.listdir(benchmark_dir) if f.endswith('.json') and f != 'summary.json']
        graph_files.sort()
        
        for i, filename in enumerate(graph_files[:max_graphs]):
            try:
                G = load_graph_from_json(os.path.join(benchmark_dir, filename))
                graphs.append(G)
            except Exception as e:
                print(f"Erreur chargement {filename}: {e}")
                continue
                
    except FileNotFoundError:
        print(f"Erreur: Dossier {benchmark_dir} non trouvé")
        return []
    
    print(f"📊 Chargé {len(graphs)} graphes depuis {benchmark_dir}")
    return graphs

def validate_coloring(G: nx.Graph, coloring: Dict[int, int]) -> bool:
    """Validate that a coloring is proper (no adjacent nodes share colors)"""
    for edge in G.edges():
        u, v = edge
        if u in coloring and v in coloring:
            if coloring[u] == coloring[v]:
                return False
    return True

def evaluate_heuristic(heuristic_module, benchmark_graphs: List[nx.Graph], 
                      max_time_per_graph: float = 1.0) -> Dict[str, Any]:
    """
    Evaluate a single graph coloring heuristic on the benchmark.
    
    Args:
        heuristic_module: Imported heuristic module
        benchmark_graphs: List of NetworkX graphs to test
        max_time_per_graph: Maximum time allowed per graph (seconds)
        
    Returns:
        Dictionary with evaluation results
    """
    results = {
        'heuristic_name': heuristic_module.get_heuristic_name(),
        'total_graphs': len(benchmark_graphs),
        'valid_colorings': 0,
        'invalid_colorings': 0,
        'timeout_graphs': 0,
        'total_time': 0.0,
        'average_time_per_graph': 0.0,
        'total_colors_used': 0,
        'min_colors_used': float('inf'),
        'max_colors_used': 0,
        'color_balance_scores': [],
        'enhanced_score': 0.0,
        'graph_results': []
    }
    
    for i, G in enumerate(benchmark_graphs):
        start_time = time.time()
        
        try:
            # Attempt to color the graph
            coloring = heuristic_module.color_graph(G)
            elapsed = time.time() - start_time
            
            if elapsed >= max_time_per_graph:
                results['timeout_graphs'] += 1
                status = 'timeout'
                colors_used = len(G.nodes())  # Worst case
                valid = False
                
            else:
                # Validate coloring
                valid = validate_coloring(G, coloring)
                colors_used = len(set(coloring.values())) if coloring else len(G.nodes())
                
                if valid:
                    results['valid_colorings'] += 1
                    status = 'valid'
                    
                    # Calculate color balance (how evenly distributed colors are)
                    if colors_used > 0:
                        color_counts = list(coloring.values())
                        color_distribution = [color_counts.count(c) for c in set(color_counts)]
                        balance_score = 1.0 - (np.std(color_distribution) / np.mean(color_distribution)) if np.mean(color_distribution) > 0 else 0.0
                        results['color_balance_scores'].append(balance_score)
                else:
                    results['invalid_colorings'] += 1
                    status = 'invalid'
            
            # Update statistics
            results['total_time'] += min(elapsed, max_time_per_graph)
            results['total_colors_used'] += colors_used
            results['min_colors_used'] = min(results['min_colors_used'], colors_used)
            results['max_colors_used'] = max(results['max_colors_used'], colors_used)
            
        except Exception as e:
            results['invalid_colorings'] += 1
            elapsed = time.time() - start_time
            status = f'error: {str(e)}'
            colors_used = len(G.nodes())
        
        results['graph_results'].append({
            'graph_index': i,
            'graph_name': G.name,
            'graph_nodes': G.number_of_nodes(),
            'graph_edges': G.number_of_edges(),
            'status': status,
            'colors_used': colors_used,
            'time': min(elapsed, max_time_per_graph),
            'valid': valid if 'valid' in locals() else False
        })
    
    # Calculate derived metrics
    if results['total_graphs'] > 0:
        results['average_time_per_graph'] = results['total_time'] / results['total_graphs']
        results['average_colors_used'] = results['total_colors_used'] / results['total_graphs']
        results['success_rate'] = results['valid_colorings'] / results['total_graphs']
        
        # Calculate color balance average
        if results['color_balance_scores']:
            results['average_color_balance'] = np.mean(results['color_balance_scores'])
        else:
            results['average_color_balance'] = 0.0
        
        # Enhanced scoring formula (NEW)
        # Lower is better for colors, higher is better for success rate and balance
        results['enhanced_score'] = (
            1000 * results['success_rate']  # Reward valid colorings
            + 100 * results['average_color_balance']  # Reward balanced colorings
            - 10 * results['average_colors_used']  # Penalize using too many colors
            - results['total_time']  # Penalize slow execution
        )
    else:
        results['success_rate'] = 0.0
        results['average_colors_used'] = 0.0
        results['average_color_balance'] = 0.0
        results['enhanced_score'] = -10000.0
    
    return results

def evaluate_all_heuristics(heuristic_dir: str, benchmark_dir: str = "graph_benchmark", 
                           max_graphs: int = 100) -> List[Dict[str, Any]]:
    """
    Evaluate all heuristics in the directory against benchmark.
    
    Args:
        heuristic_dir: Directory containing heuristic files
        benchmark_dir: Directory containing benchmark graphs
        max_graphs: Maximum number of graphs to evaluate
        
    Returns:
        List of evaluation results for each heuristic
    """
    # Load benchmark graphs
    benchmark_graphs = load_benchmark(benchmark_dir, max_graphs)
    
    if not benchmark_graphs:
        print("❌ Erreur: Aucun graphe chargé")
        return []
    
    # Load heuristic modules
    heuristic_files = [f for f in os.listdir(heuristic_dir) 
                       if f.endswith('.py') and not f.startswith('__')]
    
    all_results = []
    
    for heuristic_file in heuristic_files:
        heuristic_path = os.path.join(heuristic_dir, heuristic_file)
        module_name = heuristic_file[:-3]  # Remove .py extension
        
        try:
            # Load heuristic module
            spec = importlib.util.spec_from_file_location(module_name, heuristic_path)
            heuristic_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(heuristic_module)
            
            print(f"🧪 Évaluation de {heuristic_file}...")
            
            # Evaluate heuristic
            result = evaluate_heuristic(heuristic_module, benchmark_graphs)
            result['heuristic_file'] = heuristic_file
            result['benchmark_size'] = len(benchmark_graphs)
            all_results.append(result)
            
            print(f"✅ {heuristic_file}: Score={result['enhanced_score']:.2f}, "
                  f"Couleurs={result['average_colors_used']:.1f}, "
                  f"Succès={result['success_rate']:.2%}")
            
        except Exception as e:
            print(f"❌ Erreur chargement {heuristic_file}: {e}")
            continue
    
    return all_results

def save_evaluation_log(results: List[Dict[str, Any]], filename: str) -> None:
    """Save evaluation results to JSON file"""
    # Prepare results for JSON serialization
    json_results = []
    for result in results:
        json_result = result.copy()
        # Remove non-serializable objects
        if 'graph_results' in json_result:
            del json_result['graph_results']
        json_results.append(json_result)
    
    with open(filename, 'w') as f:
        json.dump(json_results, f, indent=2)
    
    print(f"📊 Résultats sauvegardés dans {filename}")
