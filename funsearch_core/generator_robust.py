"""
Robust FunSearch Generator for Graph Coloring heuristics
"""

import os
import json
import pathlib
import random
import time
import re
from typing import List, Optional
from api_client import LLMAPIClient
from rate_limit_handler import rate_limiter


class RobustFunSearchGenerator:
    """
    Version robuste du générateur avec validation flexible
    """
    
    def __init__(self, prompt_path: pathlib.Path, provider: str = "mistral", api_key: str = None):
        self.prompt = prompt_path.read_text(encoding="utf-8") if prompt_path.exists() else ""
        self.api_client = LLMAPIClient(provider, api_key)
        self.provider = provider
        
    def generate_candidates(self, previous_solutions: Optional[List[str]] = None, n: int = 3) -> List[str]:
        """Générer des candidats avec validation flexible"""
        print(f"🤖 Génération robuste via {self.provider.upper()}...")
        
        candidates = []
        for i in range(n):
            try:
                temperature = 0.3 + (i * 0.2)
                print(f"  🧠 Candidat {i+1}/{n} (temp={temperature:.1f})...")
                
                # Génération avec retry
                code = self._generate_with_retry(previous_solutions, temperature)
                
                if code and self._validate_flexible(code):
                    candidates.append(code)
                    print(f"  ✅ Candidat {i+1} validé")
                else:
                    print(f"  ❌ Candidat {i+1} invalide")
                    
            except Exception as e:
                print(f"  ❌ Erreur candidat {i+1}: {e}")
                continue
        
        print(f"🎉 Génération: {len(candidates)}/{n} candidats valides")
        return candidates
    
    def _generate_with_retry(self, previous_solutions: List[str], temperature: float) -> str:
        """Génération avec retry automatique"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                # Rate limit prevention
                rate_limiter.wait_if_needed()
                
                prompt = self._build_prompt(previous_solutions)
                
                code = self.api_client.generate_code(
                    prompt=prompt,
                    previous_solutions=previous_solutions,
                    temperature=min(temperature + attempt * 0.2, 0.9),
                    max_tokens=2000
                )
                
                return self._extract_code_robust(code)
                
            except Exception as e:
                error_msg = str(e)
                print(f"    ⚠️  Tentative {attempt+1}/{max_retries}: {error_msg}")
                
                # Handle rate limit specifically
                if rate_limiter.handle_rate_limit_error(error_msg):
                    continue  # Retry with backoff
                
                if attempt == max_retries - 1:
                    raise
        
        return ""
    
    def _build_prompt(self, previous_solutions: List[str]) -> str:
        """Construire le prompt avec instructions claires"""
        prompt = self.prompt
        
        if previous_solutions:
            prompt += "\n\nPrevious best solutions (for inspiration):\n"
            for i, sol in enumerate(previous_solutions[:2]):
                prompt += f"\n--- Solution {i+1} ---\n{sol[:500]}...\n"
        
        prompt += """
        
IMPORTANT INSTRUCTIONS:
1. Generate COMPLETE, WORKING Python code
2. Include ALL required functions: color_graph(G), get_heuristic_name(), get_heuristic_description()
3. Each function MUST have a proper body (not just docstring)
4. Use NetworkX for graph operations
5. Return a dictionary {node: color}
6. NO markdown fences, NO explanations, ONLY code
"""
        
        return prompt
    
    def _extract_code_robust(self, raw_code: str) -> str:
        """Extraction robuste du code"""
        # Supprimer markdown
        code = re.sub(r'```python\n?', '', raw_code)
        code = re.sub(r'```\n?', '', code)
        
        # Garder tout le code entre les fonctions
        lines = code.split('\n')
        code_lines = []
        
        for line in lines:
            # Garder les lignes qui ressemblent à du code
            if (line.strip() and 
                (line.startswith('#') or 
                 line.startswith('import') or 
                 line.startswith('from') or 
                 'def ' in line or 
                 line.strip().startswith('return') or
                 line.strip().startswith('if ') or
                 line.strip().startswith('for ') or
                 line.strip().startswith('while ') or
                 line.strip().startswith('else:') or
                 '=' in line or
                 line.strip().startswith('try:') or
                 line.strip().startswith('except') or
                 line.strip().startswith('with ') or
                 line.strip().startswith('pass'))):
                code_lines.append(line)
        
        return '\n'.join(code_lines)
    
    def _validate_flexible(self, code: str) -> bool:
        """Validation flexible du code"""
        # Vérifier les fonctions requises
        required_functions = ["color_graph", "get_heuristic_name", "get_heuristic_description"]
        
        for func in required_functions:
            if f"def {func}" not in code:
                return False
        
        # Vérifier les imports
        if "import networkx" not in code and "import nx" not in code:
            return False
        
        # Vérifier qu'il y a du code après les définitions
        lines_after_defs = []
        in_function = False
        
        for line in code.split('\n'):
            if 'def ' in line:
                in_function = True
                continue
            elif in_function and line.strip():
                lines_after_defs.append(line.strip())
        
        # Au moins 5 lignes de code après les définitions
        return len(lines_after_defs) >= 5
    
    def save_heuristic(self, code: str, cycle: int, candidate_id: int) -> str:
        """Sauvegarder une heuristique valide"""
        # Extraire le nom
        name_match = re.search(r'def get_heuristic_name.*?return\s*"([^"]+)"', code, re.DOTALL)
        heuristic_name = name_match.group(1) if name_match else f"heuristic_cycle{cycle}_candidate{candidate_id}"
        
        # Nom unique
        unique_name = f"{heuristic_name}_{cycle}_{candidate_id}"
        unique_name = re.sub(r'[^a-zA-Z0-9_]', '_', unique_name)
        
        # Préparer le code avec fonctions uniques
        formatted_code = f'''
# Heuristic: {unique_name}
def color_graph_{unique_name}(G):
    """Graph coloring heuristic"""
{self._extract_function_body(code, 'color_graph')}

def get_heuristic_name_{unique_name}():
    """Get heuristic name"""
{self._extract_function_body(code, 'get_heuristic_name')}

def get_heuristic_description_{unique_name}():
    """Get heuristic description"""
{self._extract_function_body(code, 'get_heuristic_description')}
'''
        
        # Sauvegarder
        collection_file = pathlib.Path("heuristics/heuristic_collection_working.py")
        
        if not collection_file.exists():
            header = '''"""
Working collection of Graph Coloring heuristics
"""

import networkx as nx
from typing import Dict
import random

'''
            collection_file.write_text(header)
        
        with open(collection_file, 'a', encoding='utf-8') as f:
            f.write(formatted_code)
        
        print(f"✅ Heuristic '{unique_name}' sauvegardée")
        return unique_name
    
    def _extract_function_body(self, code: str, function_name: str) -> str:
        """Extraire le corps d'une fonction"""
        pattern = rf'def {function_name}\([^)]*\):\s*(.*?)(?=\ndef|\Z)'
        match = re.search(pattern, code, re.DOTALL)
        
        if not match:
            return "    pass  # Function not found"
        
        body = match.group(1).strip()
        
        # Indenter correctement
        lines = body.split('\n')
        indented = []
        for line in lines:
            if line.strip():
                indented.append(f"    {line}")
            else:
                indented.append("")
        
        return '\n'.join(indented)


def test_robust_generator():
    """Test du générateur robuste"""
    try:
        generator = RobustFunSearchGenerator(
            pathlib.Path("prompts/llm_prompt_graph_coloring.txt"),
            "mistral"
        )
        
        print("🧪 Test générateur robuste...")
        candidates = generator.generate_candidates(n=2)
        
        if candidates:
            print("✅ Test réussi !")
            for i, code in enumerate(candidates):
                print(f"\n--- Candidat {i+1} ---")
                print(code[:300] + "..." if len(code) > 300 else code)
        else:
            print("❌ Test échoué")
            
    except Exception as e:
        print(f"❌ Erreur test: {e}")


if __name__ == "__main__":
    test_robust_generator()
