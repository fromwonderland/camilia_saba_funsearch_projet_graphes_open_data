"""
Graph solver with pluggable coloring heuristics
"""

import time
import networkx as nx
from typing import Dict, Any, Optional
import numpy as np

class GraphColoringSolver:
    """
    Graph coloring solver that uses a heuristic to assign colors to nodes.
    """
    
    def __init__(self, heuristic_func: callable):
        """
        Initialize the solver with a heuristic function.
        
        Args:
            heuristic_func: Function that takes a NetworkX graph and returns {node: color} dict
        """
        self.heuristic_func = heuristic_func
        self.nodes_processed = 0
        self.colors_used = 0
        self.execution_time = 0.0
    
    def solve(self, graph: nx.Graph, max_time: float = 1.0) -> Optional[Dict[int, int]]:
        """
        Solve the graph coloring problem using the heuristic.
        
        Args:
            graph: NetworkX graph to color
            max_time: Maximum time allowed for solving
            
        Returns:
            Dictionary mapping nodes to colors, or None if failed
        """
        start_time = time.time()
        
        try:
            # Apply the heuristic
            coloring = self.heuristic_func(graph)
            
            # Update statistics
            self.execution_time = time.time() - start_time
            self.nodes_processed = len(coloring) if coloring else 0
            self.colors_used = len(set(coloring.values())) if coloring else 0
            
            # Check if we exceeded time limit
            if self.execution_time > max_time:
                return None
            
            return coloring
            
        except Exception as e:
            self.execution_time = time.time() - start_time
            print(f"Erreur lors du coloration: {e}")
            return None
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get solver statistics."""
        return {
            'nodes_processed': self.nodes_processed,
            'colors_used': self.colors_used,
            'execution_time': self.execution_time
        }
    
    def reset_stats(self) -> None:
        """Reset solver statistics."""
        self.nodes_processed = 0
        self.colors_used = 0
        self.execution_time = 0.0

class GraphValidator:
    """Utility class for validating graph colorings."""
    
    @staticmethod
    def is_valid_coloring(graph: nx.Graph, coloring: Dict[int, int]) -> bool:
        """
        Check if a coloring is valid (no adjacent nodes share colors).
        
        Args:
            graph: NetworkX graph
            coloring: Dictionary mapping nodes to colors
            
        Returns:
            True if coloring is valid, False otherwise
        """
        # Check all edges
        for edge in graph.edges():
            u, v = edge
            if u in coloring and v in coloring:
                if coloring[u] == coloring[v]:
                    return False
        return True
    
    @staticmethod
    def count_colors_used(coloring: Dict[int, int]) -> int:
        """Count the number of unique colors used."""
        return len(set(coloring.values())) if coloring else 0
    
    @staticmethod
    def calculate_color_balance(coloring: Dict[int, int]) -> float:
        """
        Calculate how balanced the coloring is.
        
        Returns:
            Balance score between 0 (unbalanced) and 1 (perfectly balanced)
        """
        if not coloring:
            return 0.0
        
        color_counts = {}
        for color in coloring.values():
            color_counts[color] = color_counts.get(color, 0) + 1
        
        counts = list(color_counts.values())
        if not counts:
            return 0.0
        
        # Calculate coefficient of variation (lower is more balanced)
        mean_count = np.mean(counts)
        if mean_count == 0:
            return 0.0
        
        std_count = np.std(counts)
        cv = std_count / mean_count
        
        # Convert to balance score (higher is more balanced)
        balance_score = max(0.0, 1.0 - cv)
        return balance_score
    
    @staticmethod
    def analyze_coloring(graph: nx.Graph, coloring: Dict[int, int]) -> Dict[str, Any]:
        """
        Comprehensive analysis of a graph coloring.
        
        Returns:
            Dictionary with analysis metrics
        """
        if not coloring:
            return {
                'valid': False,
                'colors_used': 0,
                'coverage': 0.0,
                'balance': 0.0,
                'error': 'No coloring provided'
            }
        
        valid = GraphValidator.is_valid_coloring(graph, coloring)
        colors_used = GraphValidator.count_colors_used(coloring)
        coverage = len(coloring) / len(graph.nodes()) if len(graph.nodes()) > 0 else 0.0
        balance = GraphValidator.calculate_color_balance(coloring)
        
        return {
            'valid': valid,
            'colors_used': colors_used,
            'coverage': coverage,
            'balance': balance,
            'nodes_colored': len(coloring),
            'total_nodes': len(graph.nodes()),
            'uncolored_nodes': len(graph.nodes()) - len(coloring)
        }
