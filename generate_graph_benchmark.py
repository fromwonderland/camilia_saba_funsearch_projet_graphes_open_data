"""
Generate benchmark graphs for graph coloring FunSearch
"""

import networkx as nx
import numpy as np
import json
import random
from typing import List, Dict, Any

def generate_random_graphs(num_graphs: int = 100, min_nodes: int = 50, max_nodes: int = 200) -> List[nx.Graph]:
    """Generate random Erdős–Rényi graphs"""
    graphs = []
    for i in range(num_graphs):
        n = random.randint(min_nodes, max_nodes)
        p = random.uniform(0.1, 0.3)  # Edge probability
        G = nx.erdos_renyi_graph(n, p)
        G.name = f"random_{i}_n{n}_p{p:.2f}"
        graphs.append(G)
    return graphs

def generate_planar_graphs(num_graphs: int = 50) -> List[nx.Graph]:
    """Generate planar graphs"""
    graphs = []
    for i in range(num_graphs):
        n = random.randint(20, 100)
        # Triangular lattice for planar graphs
        G = nx.triangular_lattice_graph(int(np.sqrt(n)), int(np.sqrt(n)))
        G.name = f"planar_{i}_n{G.number_of_nodes()}"
        graphs.append(G)
    return graphs

def generate_scale_free_graphs(num_graphs: int = 50) -> List[nx.Graph]:
    """Generate scale-free networks"""
    graphs = []
    for i in range(num_graphs):
        n = random.randint(50, 200)
        m = random.randint(2, 5)  # Number of edges to attach from a new node
        G = nx.barabasi_albert_graph(n, m)
        G.name = f"scalefree_{i}_n{n}_m{m}"
        graphs.append(G)
    return graphs

def generate_small_world_graphs(num_graphs: int = 50) -> List[nx.Graph]:
    """Generate small-world networks"""
    graphs = []
    for i in range(num_graphs):
        n = random.randint(50, 200)
        k = random.randint(4, 10)  # Each node connected to k nearest neighbors
        p = random.uniform(0.1, 0.3)  # Probability of rewiring
        G = nx.watts_strogatz_graph(n, k, p)
        G.name = f"smallworld_{i}_n{n}_k{k}_p{p:.2f}"
        graphs.append(G)
    return graphs

def save_graph_to_json(G: nx.Graph, filename: str) -> None:
    """Save graph to JSON format"""
    data = {
        'name': G.name,
        'nodes': list(G.nodes()),
        'edges': list(G.edges()),
        'num_nodes': G.number_of_nodes(),
        'num_edges': G.number_of_edges(),
        'density': nx.density(G),
        'type': 'unknown'
    }
    
    # Detect graph type
    if nx.is_planar(G):
        data['type'] = 'planar'
    elif nx.is_connected(G) and max(dict(G.degree()).values()) > len(G.nodes()) * 0.8:
        data['type'] = 'scale_free'
    elif nx.average_clustering(G) > 0.3:
        data['type'] = 'small_world'
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)

def generate_benchmark():
    """Generate complete benchmark suite"""
    print("🎨 Génération du benchmark Graph Coloring...")
    
    # Generate different types of graphs
    random_graphs = generate_random_graphs(100, 50, 200)
    planar_graphs = generate_planar_graphs(50)
    scale_free_graphs = generate_scale_free_graphs(50)
    small_world_graphs = generate_small_world_graphs(50)
    
    all_graphs = random_graphs + planar_graphs + scale_free_graphs + small_world_graphs
    
    print(f"📊 Total: {len(all_graphs)} graphes générés")
    print(f"   - Random: {len(random_graphs)}")
    print(f"   - Planar: {len(planar_graphs)}")
    print(f"   - Scale-free: {len(scale_free_graphs)}")
    print(f"   - Small-world: {len(small_world_graphs)}")
    
    # Save all graphs
    benchmark_dir = "graph_benchmark"
    import os
    os.makedirs(benchmark_dir, exist_ok=True)
    
    for i, G in enumerate(all_graphs):
        filename = f"{benchmark_dir}/graph_{i:03d}.json"
        save_graph_to_json(G, filename)
    
    # Save benchmark summary
    summary = {
        'total_graphs': len(all_graphs),
        'types': {
            'random': len(random_graphs),
            'planar': len(planar_graphs),
            'scale_free': len(scale_free_graphs),
            'small_world': len(small_world_graphs)
        },
        'node_range': [50, 200],
        'description': 'Graph coloring benchmark with diverse graph types'
    }
    
    with open(f"{benchmark_dir}/summary.json", 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"✅ Benchmark sauvegardé dans {benchmark_dir}/")
    print(f"📈 Fichier résumé: {benchmark_dir}/summary.json")

if __name__ == "__main__":
    generate_benchmark()
