"""
Token bucket rate limiter with in-memory state.
Fail-open: Allow on error.
"""

import time
from typing import Tuple, Dict


class RateLimiter:
    """Token bucket rate limiter (in-memory)."""
    
    def __init__(self, requests_per_minute: int = 100):
        self.max_tokens = 120  # burst size
        self.refill_rate = requests_per_minute / 60.0  # tokens per second
        self.state: Dict[str, Tuple[float, float]] = {}  # key -> (tokens, last_update)
    
    def is_allowed(self) -> bool:
        """
        Check if request is within rate limit.
        Global rate limiting (simplified).
        """
        try:
            now = time.time()
            key = "global"
            
            if key not in self.state:
                # First request
                self.state[key] = (self.max_tokens - 1, now)
                return True
            
            tokens, last_update = self.state[key]
            
            # Calculate token refill
            elapsed = now - last_update
            tokens = min(self.max_tokens, tokens + elapsed * self.refill_rate)
            
            if tokens < 1:
                # Rate limit exceeded
                self.state[key] = (tokens, now)
                return False
            
            # Consume 1 token
            self.state[key] = (tokens - 1, now)
            return True
            
        except Exception:
            # Fail-open: Allow on error
            return True