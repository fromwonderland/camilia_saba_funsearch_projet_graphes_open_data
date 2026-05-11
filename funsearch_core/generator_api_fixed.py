"""
FunSearch Generator for Graph Coloring heuristics using API LLMs - FIXED VERSION

Generates new graph coloring heuristics using premium LLM APIs with proper code extraction.
"""

from __future__ import annotations
import os
import json
import pathlib
import random
import time
import hashlib
import textwrap
import re
from typing import List, Optional
from api_client import LLMAPIClient


class FunSearchAPIGeneratorFixed:
    """
    FIXED Generator using API-based LLMs for FunSearch evolution
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
        
    def generate_candidates(self, previous_solutions: Optional[List[str]] = None, n: int = 5) -> List[str]:
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
                temperature = 0.2 + (i * 0.15)  # 0.2, 0.35, 0.5, 0.65, 0.8
                
                print(f"  🧠 Génération candidat {i+1}/{n} (temp={temperature:.2f})...")
                
                # Générer via API
                code = self.api_client.generate_code(
                    prompt=self.prompt,
                    previous_solutions=previous_solutions,
                    temperature=temperature,
                    max_tokens=2000  # Augmenté pour code complet
                )
                
                # Nettoyer et extraire le code généré
                cleaned_code = self._extract_complete_code(code)
                
                if cleaned_code and self._validate_complete_code(cleaned_code):
                    candidates.append(cleaned_code)
                    print(f"  ✅ Candidat {i+1} généré avec succès")
                else:
                    print(f"  ❌ Candidat {i+1} invalide - retry with higher temperature...")
                    # Retry with higher temperature
                    try:
                        retry_code = self.api_client.generate_code(
                            prompt=self.prompt + "\n\nIMPORTANT: Provide complete, working code with all function bodies implemented.",
                            previous_solutions=previous_solutions,
                            temperature=0.9,
                            max_tokens=2500
                        )
                        retry_cleaned = self._extract_complete_code(retry_code)
                        if retry_cleaned and self._validate_complete_code(retry_cleaned):
                            candidates.append(retry_cleaned)
                            print(f"  ✅ Candidat {i+1} généré avec succès (retry)")
                        else:
                            print(f"  ❌ Candidat {i+1} définitivement invalide")
                    except Exception as retry_e:
                        print(f"  ❌ Retry échoué: {retry_e}")
                    
            except Exception as e:
                print(f"  ❌ Erreur génération candidat {i+1}: {e}")
                continue
        
        print(f"🎉 Génération terminée: {len(candidates)}/{n} candidats valides")
        return candidates
    
    def _extract_complete_code(self, raw_code: str) -> str:
        """
        Extraire et nettoyer le code complet généré par l'API
        
        Args:
            raw_code: Code brut de l'API
            
        Returns:
            Code complet et nettoyé
        """
        # Supprimer les balises markdown
        code = re.sub(r'```python\n?', '', raw_code)
        code = re.sub(r'```\n?', '', code)
        
        # Supprimer les explications textuelles
        lines = code.split('\n')
        code_lines = []
        
        for line in lines:
            line = line.strip()
            # Garder les lignes de code et commentaires
            if line and (line.startswith('#') or line.startswith('import') or 
                        line.startswith('from') or 'def ' in line or 
                        line.startswith(' ') or line.startswith('\t') or
                        line.startswith('return') or line.startswith('if ') or
                        line.startswith('for ') or line.startswith('while ') or
                        line.startswith('else:') or line.startswith('elif ') or
                        line.startswith('try:') or line.startswith('except') or
                        line.startswith('finally:') or line.startswith('with ') or
                        '=' in line or '[' in line or '(' in line or '{' in line):
                code_lines.append(line)
        
        return '\n'.join(code_lines)
    
    def _validate_complete_code(self, code: str) -> bool:
        """
        Valider que le code contient toutes les fonctions requises avec corps
        
        Args:
            code: Code à valider
            
        Returns:
            True si le code est complet et valide
        """
        required_functions = ["color_graph", "get_heuristic_name", "get_heuristic_description"]
        
        for func in required_functions:
            # Vérifier que la fonction existe et a un corps
            pattern = rf'def {func}\([^)]*\):\s*(.*?)(?=\ndef|\Z)'
            match = re.search(pattern, code, re.DOTALL)
            
            if not match:
                return False
            
            # Vérifier que le corps n'est pas vide
            body = match.group(1).strip()
            if not body or body == '"""' or len(body) < 10:
                return False
        
        # Vérifier l'import de networkx
        if "import networkx" not in code and "import nx" not in code:
            return False
        
        return True
    
    def save_heuristic_to_collection(self, code: str, cycle: int, candidate_id: int) -> str:
        """
        Sauvegarder une heuristique complète dans la collection
        
        Args:
            code: Code complet de l'heuristique
            cycle: Numéro du cycle
            candidate_id: ID du candidat
            
        Returns:
            Nom unique de l'heuristique
        """
        # Extraire le nom de l'heuristique
        try:
            name_match = re.search(r'get_heuristic_name\(\)\s*->\s*str:\s*return\s*"([^"]+)"', code, re.DOTALL)
            if name_match:
                heuristic_name = name_match.group(1)
            else:
                # Fallback: chercher dans une autre forme
                name_match = re.search(r'def get_heuristic_name.*?return\s*"([^"]+)"', code, re.DOTALL)
                heuristic_name = name_match.group(1) if name_match else f"heuristic_cycle{cycle}_candidate{candidate_id}"
        except:
            heuristic_name = f"heuristic_cycle{cycle}_candidate{candidate_id}"
        
        # Créer un nom unique
        unique_name = f"{heuristic_name}_{cycle}_{candidate_id}"
        unique_name = re.sub(r'[^a-zA-Z0-9_]', '_', unique_name)  # Nettoyer le nom
        
        # Préparer le code avec fonctions uniques
        formatted_code = f'''
# Heuristic: {unique_name} (Cycle {cycle}, Candidate {candidate_id})
def color_graph_{unique_name}(G):
    """Generated graph coloring heuristic"""
{self._extract_function_body(code, 'color_graph')}

def get_heuristic_name_{unique_name}():
    """Get heuristic name"""
{self._extract_function_body(code, 'get_heuristic_name')}

def get_heuristic_description_{unique_name}():
    """Get heuristic description"""
{self._extract_function_body(code, 'get_heuristic_description')}
'''
        
        # Ajouter à la collection
        collection_file = pathlib.Path("heuristics/heuristic_collection_fixed.py")
        
        # Créer le fichier s'il n'existe pas
        if not collection_file.exists():
            header = '''"""
Collection of generated Graph Coloring heuristics
"""

import networkx as nx
from typing import Dict
import random

'''
            collection_file.write_text(header)
        
        # Ajouter à la collection
        with open(collection_file, 'a', encoding='utf-8') as f:
            f.write(formatted_code)
        
        print(f"✅ Heuristic '{unique_name}' added to collection")
        return unique_name
    
    def _extract_function_body(self, code: str, function_name: str) -> str:
        """
        Extraire le corps complet d'une fonction du code généré
        
        Args:
            code: Code complet
            function_name: Nom de la fonction à extraire
            
        Returns:
            Corps de la fonction correctement indenté
        """
        # Pattern pour capturer la fonction complète
        pattern = rf'def {function_name}\([^)]*\):\s*(.*?)(?=\ndef|\Z)'
        match = re.search(pattern, code, re.DOTALL)
        
        if not match:
            return "    pass  # Function not found"
        
        body = match.group(1).strip()
        
        # Nettoyer le corps et ajouter une indentation correcte
        lines = body.split('\n')
        indented_lines = []
        
        for line in lines:
            if line.strip():
                indented_lines.append(f"    {line}")
            else:
                indented_lines.append("")
        
        return '\n'.join(indented_lines)


# Configuration pour tests rapides
def test_api_generator_fixed():
    """Test rapide du générateur API corrigé"""
    try:
        generator = FunSearchAPIGeneratorFixed(
            pathlib.Path("prompts/llm_prompt_graph_coloring.txt"),
            provider="mistral"
        )
        
        print("🧪 Test du générateur API corrigé...")
        candidates = generator.generate_candidates(n=1)
        
        if candidates:
            print("✅ Test réussi !")
            print("Code généré (premières lignes):")
            lines = candidates[0].split('\n')[:10]
            for line in lines:
                print(f"  {line}")
        else:
            print("❌ Test échoué")
            
    except Exception as e:
        print(f"❌ Erreur test: {e}")
        print("Assurez-vous d'avoir configuré la clé API:")
        print("export MISTRAL_API_KEY='votre_clé'")

if __name__ == "__main__":
    test_api_generator_fixed()
