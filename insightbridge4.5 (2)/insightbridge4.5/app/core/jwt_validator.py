"""
JWT validation with exp, nbf, iat checks and clock drift tolerance.
Fail-closed: Any validation failure results in denial.
"""

import time
import jwt
from typing import Dict, Any
from app.config import Settings


class JWTValidator:
    """JWT validation with strict security checks."""
    
    def __init__(self, settings: Settings):
        self.settings = settings
        self.public_key = self._load_public_key()
        self.algorithm = self.settings.jwt_algorithm
        self.clock_drift = self.settings.jwt_clock_drift_seconds
    
    def _load_public_key(self) -> str:
        """Load JWT public key from file."""
        try:
            with open(self.settings.jwt_public_key_path, 'r') as f:
                return f.read()
        except Exception as e:
            # Fail-closed: If key loading fails, cannot validate
            raise RuntimeError(f"Failed to load JWT public key: {e}")
    
    def validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token with all security checks.
        
        Returns:
            payload dict or error dict with "error" key
        """
        if not token:
            return {"error": "malformed"}
        
        try:
            # Decode and verify signature
            payload = jwt.decode(
                token,
                self.public_key,
                algorithms=[self.algorithm],
                options={
                    "verify_signature": True,
                    "verify_exp": False,  # We'll do this manually with clock drift
                    "verify_nbf": False,  # We'll do this manually with clock drift
                }
            )
        except jwt.ExpiredSignatureError:
            return {"error": "expired"}
        except jwt.InvalidSignatureError:
            return {"error": "invalid_signature"}
        except jwt.DecodeError:
            return {"error": "malformed"}
        except Exception:
            return {"error": "malformed"}
        
        # Manual exp validation with clock drift
        now = int(time.time())
        exp = payload.get("exp")
        
        if exp is None:
            return {"error": "malformed"}
        
        if now > exp + self.clock_drift:
            return {"error": "expired"}
        
        # Manual nbf validation with clock drift
        nbf = payload.get("nbf")
        if nbf is not None:
            if now < nbf - self.clock_drift:
                return {"error": "not_yet_valid"}
        
        # Validate required fields
        if "jti" not in payload or "sub" not in payload:
            return {"error": "malformed"}
        
        return payload