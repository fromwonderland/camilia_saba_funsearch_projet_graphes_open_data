"""
FunSearch Generator for Graph Coloring heuristics using API LLMs

Generates new graph coloring heuristics using premium LLM APIs.
"""

from __future__ import annotations
import os
import json
import pathlib
import random
import time
import hashlib
import textwrap
from typing import List, Optional
from funsearch_core.api_client import LLMAPIClient


class FunSearchAPIGenerator:
    """
    Generator using API-based LLMs for FunSearch evolution
    """
    
    def __init__(self, prompt_path: pathlib.Path, provider: str = "mistral", api_key: str = None):
        """
        Initialize the generator with API configuration.
        
        Args:
            prompt_path: Path to the prompt template file
            provider: LLM provider ("mistral", "openai", "claude")
            api_key: API key (optional, can be set via environment variable)
        """
        # Load prompt
        if prompt_path.exists():
            self.prompt = prompt_path.read_text(encoding="utf-8")
        else:
            raise FileNotFoundError(f"Prompt file not found: {prompt_path}")
        
        # Initialize API client
        self.api_client = LLMAPIClient(provider, api_key)
        self.provider = provider
        
    def generate_candidates(self, previous_solutions: Optional[List[str]] = None, n: int = 3) -> List[str]:
        """
        Generate candidate heuristics using API LLM.
        
        Args:
            previous_solutions: List of previous best solutions for improvement
            n: Number of candidates to generate
            
        Returns:
            List of generated heuristic code strings
        """
        print(f"🤖 Génération via API {self.provider.upper()}...")
        
        candidates = []
        for i in range(n):
            try:
                # Varier la température pour la diversité
                temperature = 0.3 + (i * 0.2)  # 0.3, 0.5, 0.7
                
                print(f"  🧠 Génération candidat {i+1}/{n} (temp={temperature:.1f})...")
                
                # Générer via API
                code = self.api_client.generate_code(
                    prompt=self.prompt,
                    previous_solutions=previous_solutions,
                    temperature=temperature,
                    max_tokens=1500
                )
                
                # Nettoyer le code généré
                cleaned_code = self._clean_generated_code(code)
                
                if cleaned_code and self._validate_code_structure(cleaned_code):
                    candidates.append(cleaned_code)
                    print(f"  ✅ Candidat {i+1} généré avec succès")
                else:
                    print(f"  ❌ Candidat {i+1} invalide")
                    
            except Exception as e:
                print(f"  ❌ Erreur génération candidat {i+1}: {e}")
                continue
        
        print(f"🎉 Génération terminée: {len(candidates)}/{n} candidats valides")
        return candidates
    
    def _clean_generated_code(self, code: str) -> str:
        """
        Nettoyer le code généré par l'API
        
        Args:
            code: Code brut de l'API
            
        Returns:
            Code nettoyé
        """
        # Supprimer les balises markdown si présentes
        code = code.replace("```python", "").replace("```", "")
        
        # Supprimer les espaces superflus
        lines = [line.strip() for line in code.split('\n') if line.strip()]
        
        return '\n'.join(lines)
    
    def _validate_code_structure(self, code: str) -> bool:
        """
        Valider la structure du code généré
        
        Args:
            code: Code à valider
            
        Returns:
            True si la structure est valide
        """
        # Vérifier la présence des fonctions requises
        required_functions = ["color_graph", "get_heuristic_name", "get_heuristic_description"]
        
        for func in required_functions:
            if f"def {func}" not in code:
                return False
        
        # Vérifier l'import de networkx
        if "import networkx" not in code and "import nx" not in code:
            return False
        
        return True
    
    def save_heuristic_to_collection(self, code: str, cycle: int, candidate_id: int) -> str:
        """
        Sauvegarder une heuristique dans la collection
        
        Args:
            code: Code de l'heuristique
            cycle: Numéro du cycle
            candidate_id: ID du candidat
            
        Returns:
            Nom unique de l'heuristique
        """
        # Extraire le nom de l'heuristique
        try:
            name_line = [line for line in code.split('\n') if 'get_heuristic_name' in line and 'return' in line][0]
            heuristic_name = name_line.split('"')[1] if '"' in name_line else f"heuristic_cycle{cycle}_candidate{candidate_id}"
        except:
            heuristic_name = f"heuristic_cycle{cycle}_candidate{candidate_id}"
        
        # Créer un nom unique
        unique_name = f"{heuristic_name}_{cycle}_{candidate_id}"
        unique_name = unique_name.replace(" ", "_").replace("-", "_")
        
        # Ajouter le code à la collection
        collection_file = pathlib.Path("heuristics/heuristic_collection_clean.py")
        
        # Créer le header si le fichier n'existe pas
        if not collection_file.exists():
            collection_file.write_text('"""Collection of generated Graph Coloring heuristics"""\n\nimport networkx as nx\nfrom typing import Dict\n\n')
        
        # Préparer le code avec fonctions uniques
        formatted_code = f'''
# Heuristic: {unique_name} (Cycle {cycle}, Candidate {candidate_id})
def color_graph_{unique_name}(G: nx.Graph) -> Dict[int, int]:
{self._extract_function_body(code, 'color_graph')}

def get_heuristic_name_{unique_name}() -> str:
{self._extract_function_body(code, 'get_heuristic_name')}

def get_heuristic_description_{unique_name}() -> str:
{self._extract_function_body(code, 'get_heuristic_description')}
'''
        
        # Ajouter à la collection
        with open(collection_file, 'a', encoding='utf-8') as f:
            f.write(formatted_code)
        
        print(f"✅ Heuristic '{unique_name}' added to collection")
        return unique_name
    
    def _extract_function_body(self, code: str, function_name: str) -> str:
        """
        Extraire le corps d'une fonction du code généré
        
        Args:
            code: Code complet
            function_name: Nom de la fonction à extraire
            
        Returns:
            Corps de la fonction indenté
        """
        lines = code.split('\n')
        in_function = False
        function_lines = []
        indent_level = 0
        
        for line in lines:
            if f"def {function_name}" in line:
                in_function = True
                # Extraire l'indentation de la première ligne après def
                if ':' in line:
                    indent_level = len(line.split(':')[1]) + 4
                continue
            
            if in_function:
                if line.strip() and not line.startswith(' ' * (indent_level - 1)) and function_lines:
                    break
                
                function_lines.append(line)
        
        if not function_lines:
            return "    pass  # Function body not found"
        
        return '\n'.join(function_lines)


# Configuration pour tests rapides
def test_api_generator():
    """Test rapide du générateur API"""
    try:
        generator = FunSearchAPIGenerator(
            pathlib.Path("prompts/llm_prompt_graph_coloring.txt"),
            provider="mistral"
        )
        
        print("🧪 Test du générateur API...")
        candidates = generator.generate_candidates(n=1)
        
        if candidates:
            print("✅ Test réussi !")
            print("Code généré:")
            print(candidates[0][:500] + "..." if len(candidates[0]) > 500 else candidates[0])
        else:
            print("❌ Test échoué")
            
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        print("Assurez-vous d'avoir configuré la clé API:")
        print("export MISTRAL_API_KEY='votre_clé'")

if __name__ == "__main__":
    test_api_generator()
