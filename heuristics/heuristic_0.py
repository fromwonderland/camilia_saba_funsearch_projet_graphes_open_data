
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
