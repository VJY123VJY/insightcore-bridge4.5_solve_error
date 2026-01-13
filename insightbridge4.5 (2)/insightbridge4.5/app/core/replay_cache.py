"""
Replay attack prevention with in-memory cache and TTL eviction.
"""

import time
from typing import Set, Tuple


class ReplayCache:
    """Replay detection with in-memory storage."""
    
    def __init__(self):
        self.seen: Set[str] = set()
        self.jti_timestamps: dict[str, float] = {}
    
    def is_replayed(self, jti: str) -> bool:
        """
        Check if JWT ID has been seen before.
        """
        if not jti:
            return True  # No JTI = invalid = deny
        
        # Cleanup expired entries periodically
        if len(self.seen) % 100 == 0:
            self._cleanup_expired()
        
        return jti in self.seen
    
    def record(self, jti: str, exp: int = None):
        """
        Mark JWT ID as seen.
        """
        if jti:
            self.seen.add(jti)
            if exp:
                self.jti_timestamps[jti] = exp
    
    def _cleanup_expired(self):
        """Remove expired JTIs from cache."""
        now = time.time()
        expired = [jti for jti, exp_time in self.jti_timestamps.items() if exp_time < now]
        for jti in expired:
            self.seen.discard(jti)
            self.jti_timestamps.pop(jti, None)
    
    def size(self) -> int:
        """Get current cache size."""
        return len(self.seen)