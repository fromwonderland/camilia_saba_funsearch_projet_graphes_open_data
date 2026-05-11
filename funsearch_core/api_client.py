"""
API Client pour LLM (Mistral, Claude, OpenAI)
"""

import os
import json
import time
from typing import List, Optional, Dict, Any
import requests
from pathlib import Path

class LLMAPIClient:
    """Client générique pour APIs LLM"""
    
    def __init__(self, provider: str = "mistral", api_key: str = None):
        """
        Initialiser le client API
        
        Args:
            provider: "mistral", "openai", "claude", "gemini"
            api_key: Clé API (si None, cherche dans variables environnement)
        """
        self.provider = provider
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")
        
        if not self.api_key:
            raise ValueError(f"Clé API {provider.upper()}_API_KEY non trouvée")
        
        # Configuration par provider
        self.configs = {
            "mistral": {
                "base_url": "https://api.mistral.ai/v1",
                "model": "mistral-large-latest",
                "endpoint": "/chat/completions"
            },
            "openai": {
                "base_url": "https://api.openai.com/v1",
                "model": "gpt-4",
                "endpoint": "/chat/completions"
            },
            "claude": {
                "base_url": "https://api.anthropic.com/v1",
                "model": "claude-3-opus-20240229",
                "endpoint": "/messages"
            }
        }
        
        self.config = self.configs.get(provider, self.configs["mistral"])
    
    def generate_code(self, prompt: str, previous_solutions: Optional[List[str]] = None, 
                   temperature: float = 0.7, max_tokens: int = 1000) -> str:
        """
        Générer du code via API
        
        Args:
            prompt: Prompt principal
            previous_solutions: Solutions précédentes pour réinjection
            temperature: Température de génération (0.0-1.0)
            max_tokens: Nombre maximum de tokens
            
        Returns:
            Code généré
        """
        # Construire le prompt complet
        full_prompt = prompt
        if previous_solutions:
            full_prompt += "\n\nPrevious best solutions (for improvement):\n"
            for i, solution in enumerate(previous_solutions[:2]):
                full_prompt += f"\nSolution {i+1}:\n{solution}\n"
        
        # Préparer la requête selon le provider
        if self.provider == "mistral":
            return self._call_mistral(full_prompt, temperature, max_tokens)
        elif self.provider == "openai":
            return self._call_openai(full_prompt, temperature, max_tokens)
        elif self.provider == "claude":
            return self._call_claude(full_prompt, temperature, max_tokens)
        else:
            raise ValueError(f"Provider {self.provider} non supporté")
    
    def _call_mistral(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Appel API Mistral"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.config["model"],
            "messages": [
                {"role": "system", "content": "You are an expert graph coloring algorithm designer. Generate only valid Python code."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False
        }
        
        response = requests.post(
            self.config["base_url"] + self.config["endpoint"],
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Erreur API Mistral: {response.status_code} - {response.text}")
    
    def _call_openai(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Appel API OpenAI"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.config["model"],
            "messages": [
                {"role": "system", "content": "You are an expert graph coloring algorithm designer. Generate only valid Python code."},
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        response = requests.post(
            self.config["base_url"] + self.config["endpoint"],
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Erreur API OpenAI: {response.status_code} - {response.text}")
    
    def _call_claude(self, prompt: str, temperature: float, max_tokens: int) -> str:
        """Appel API Claude"""
        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": self.config["model"],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "user", "content": f"You are an expert graph coloring algorithm designer. Generate only valid Python code.\n\n{prompt}"}
            ]
        }
        
        response = requests.post(
            self.config["base_url"] + self.config["endpoint"],
            headers=headers,
            json=data,
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json()["content"][0]["text"]
        else:
            raise Exception(f"Erreur API Claude: {response.status_code} - {response.text}")

# Configuration rapide
def setup_api_keys():
    """Guide pour configurer les clés API"""
    print("🔑 Configuration des clés API :")
    print("1. Mistral: https://console.mistral.ai/")
    print("   export MISTRAL_API_KEY='votre_clé'")
    print("2. OpenAI: https://platform.openai.com/")
    print("   export OPENAI_API_KEY='votre_clé'")
    print("3. Claude: https://console.anthropic.com/")
    print("   export CLAUDE_API_KEY='votre_clé'")

if __name__ == "__main__":
    setup_api_keys()
