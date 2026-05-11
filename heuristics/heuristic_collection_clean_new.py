"""
Collection of working Graph Coloring heuristics - CLEAN VERSION
"""

import networkx as nx
from typing import Dict
import random

# Baseline heuristic
def color_graph_baseline(G: nx.Graph) -> Dict[int, int]:
    """Baseline greedy coloring - nodes in order of degree"""
    if not G.nodes():
        return {}
    
    nodes_by_degree = sorted(G.nodes(), key=lambda x: G.degree(x), reverse=True)
    coloring = {}
    
    for node in nodes_by_degree:
        neighbor_colors = set()
        for neighbor in G.neighbors(node):
            if neighbor in coloring:
                neighbor_colors.add(coloring[neighbor])
        
        color = 0
        while color in neighbor_colors:
            color += 1
        
        coloring[node] = color
    
    return coloring

def get_heuristic_name_baseline() -> str:
    return "greedy_degree_baseline"

def get_heuristic_description_baseline() -> str:
    return "Baseline greedy coloring - nodes processed in order of degree"
