"""
Rate Limit Handler pour API Mistral
"""

import time
import random
from typing import Optional


class RateLimitHandler:
    """
    Gestionnaire des rate limits pour APIs
    """
    
    def __init__(self, min_delay: float = 3.0, max_delay: float = 8.0):
        self.min_delay = min_delay  # Augmenté pour version free
        self.max_delay = max_delay  # Augmenté pour version free
        self.last_request_time = 0
        self.consecutive_errors = 0
        
    def wait_if_needed(self) -> None:
        """Attendre si nécessaire pour éviter rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Délai adaptatif selon erreurs
        adaptive_delay = min(self.min_delay + (self.consecutive_errors * 0.5), self.max_delay)
        
        if time_since_last < adaptive_delay:
            wait_time = adaptive_delay - time_since_last
            print(f"⏳ Rate limit prevention: attente {wait_time:.1f}s...")
            time.sleep(wait_time)
        
        self.last_request_time = time.time()
    
    def handle_rate_limit_error(self, error_message: str) -> bool:
        """Détecter et gérer les erreurs de rate limit"""
        if "429" in error_message or "rate limit" in error_message.lower():
            self.consecutive_errors += 1
            
            # Backoff exponentiel
            backoff_time = min(2 ** self.consecutive_errors, 30)
            print(f"🚦 Rate limit détecté! Backoff {backoff_time}s...")
            time.sleep(backoff_time)
            
            return True
        else:
            # Reset si erreur différente
            self.consecutive_errors = 0
            return False
    
    def reset(self) -> None:
        """Reset le compteur d'erreurs"""
        self.consecutive_errors = 0


# Instance globale
rate_limiter = RateLimitHandler()
