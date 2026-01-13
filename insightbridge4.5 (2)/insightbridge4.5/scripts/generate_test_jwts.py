#!/usr/bin/env python3
"""
JWT Token Generator for InsightBridge v4.0
Generates signed JWT tokens for testing and development.
"""

import jwt
import time
import uuid
import os
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


class JWTTokenGenerator:
    """Generate JWT tokens with various scenarios."""
    
    def __init__(self, private_key_path="keys/private_key.pem"):
        self.private_key_path = private_key_path
        self.private_key = None
        self.load_or_generate_keys()
    
    def load_or_generate_keys(self):
        """Load existing keys or generate new ones."""
        if os.path.exists(self.private_key_path):
            print(f"✅ Loading private key from {self.private_key_path}")
            with open(self.private_key_path, "rb") as f:
                self.private_key = f.read()
        else:
            print("🔑 Generating new RSA key pair...")
            self.generate_keys()
    
    def generate_keys(self):
        """Generate RSA key pair."""
        # Create keys directory
        os.makedirs("keys", exist_ok=True)
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        
        # Get public key
        public_key = private_key.public_key()
        
        # Save private key
        with open("keys/private_key.pem", "wb") as f:
            private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            f.write(private_key_pem)
            self.private_key = private_key_pem
        
        # Save public key
        with open("keys/public_key.pem", "wb") as f:
            f.write(public_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo
            ))
        
        print("✅ Keys generated:")
        print("   - keys/private_key.pem")
        print("   - keys/public_key.pem")
    
    def generate_token(
        self,
        user_id="user123",
        jti=None,
        exp_hours=1,
        nbf_hours=0,
        algorithm="RS256",
        extra_claims=None
    ):
        """
        Generate a JWT token.
        
        Args:
            user_id: User identifier (sub claim)
            jti: JWT ID (unique identifier)
            exp_hours: Hours until expiration (negative for expired)
            nbf_hours: Hours until token becomes valid (0 = now)
            algorithm: Signing algorithm (RS256, HS256, etc.)
            extra_claims: Additional claims to include
        
        Returns:
            JWT token string
        """
        now = int(time.time())
        
        # Build payload
        payload = {
            "sub": user_id,
            "jti": jti or str(uuid.uuid4()),
            "iat": now,
            "nbf": now + (nbf_hours * 3600),
            "exp": now + (exp_hours * 3600),
        }
        
        # Add extra claims
        if extra_claims:
            payload.update(extra_claims)
        
        # Sign token
        token = jwt.encode(payload, self.private_key, algorithm=algorithm)
        
        return token
    
    def generate_valid_token(self, user_id="user123"):
        """Generate a valid token (1 hour expiry)."""
        return self.generate_token(
            user_id=user_id,
            jti=f"valid-{uuid.uuid4()}",
            exp_hours=1
        )
    
    def generate_expired_token(self, user_id="user123"):
        """Generate an expired token (expired 1 hour ago)."""
        return self.generate_token(
            user_id=user_id,
            jti=f"expired-{uuid.uuid4()}",
            exp_hours=-1
        )
    
    def generate_future_token(self, user_id="user123"):
        """Generate a token valid in the future (nbf in 1 hour)."""
        return self.generate_token(
            user_id=user_id,
            jti=f"future-{uuid.uuid4()}",
            exp_hours=2,
            nbf_hours=1
        )
    
    def generate_short_lived_token(self, user_id="user123", seconds=30):
        """Generate a short-lived token."""
        return self.generate_token(
            user_id=user_id,
            jti=f"short-{uuid.uuid4()}",
            exp_hours=seconds / 3600
        )
    
    def generate_replay_token(self, jti="replay-test-001"):
        """Generate a token for replay testing (same JTI)."""
        return self.generate_token(
            user_id="replay-user",
            jti=jti,
            exp_hours=1
        )
    
    def decode_token(self, token):
        """Decode token without verification (for inspection)."""
        return jwt.decode(token, options={"verify_signature": False})
    
    def print_token_info(self, token):
        """Print token information."""
        try:
            decoded = self.decode_token(token)
            
            print("\n📋 Token Information:")
            print("-" * 60)
            print(f"  User ID (sub):  {decoded.get('sub')}")
            print(f"  JWT ID (jti):   {decoded.get('jti')}")
            print(f"  Issued At:      {datetime.fromtimestamp(decoded.get('iat'))}")
            print(f"  Not Before:     {datetime.fromtimestamp(decoded.get('nbf'))}")
            print(f"  Expires:        {datetime.fromtimestamp(decoded.get('exp'))}")
            
            exp_time = decoded.get('exp')
            now = time.time()
            if exp_time > now:
                print(f"  Status:         ✅ Valid (expires in {int((exp_time - now) / 60)} minutes)")
            else:
                print(f"  Status:         ❌ Expired ({int((now - exp_time) / 60)} minutes ago)")
            
            print("-" * 60)
            print(f"\n🔑 Full Token:\n{token}\n")
            
        except Exception as e:
            print(f"❌ Error decoding token: {e}")


def main():
    """Main function with CLI interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Generate JWT tokens for InsightBridge testing"
    )
    
    parser.add_argument(
        "--type",
        choices=["valid", "expired", "future", "short", "replay", "custom"],
        default="valid",
        help="Type of token to generate"
    )
    
    parser.add_argument(
        "--user-id",
        default="user123",
        help="User ID (sub claim)"
    )
    
    parser.add_argument(
        "--jti",
        help="JWT ID (unique identifier)"
    )
    
    parser.add_argument(
        "--exp-hours",
        type=float,
        default=1,
        help="Hours until expiration (negative for expired)"
    )
    
    parser.add_argument(
        "--nbf-hours",
        type=float,
        default=0,
        help="Hours until token becomes valid"
    )
    
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of tokens to generate"
    )
    
    parser.add_argument(
        "--output",
        help="Output file for tokens"
    )
    
    parser.add_argument(
        "--show-info",
        action="store_true",
        help="Show decoded token information"
    )
    
    args = parser.parse_args()
    
    # Initialize generator
    generator = JWTTokenGenerator()
    
    tokens = []
    
    print(f"\n🎫 Generating {args.count} {args.type.upper()} token(s)...\n")
    
    for i in range(args.count):
        # Generate token based on type
        if args.type == "valid":
            token = generator.generate_valid_token(args.user_id)
        elif args.type == "expired":
            token = generator.generate_expired_token(args.user_id)
        elif args.type == "future":
            token = generator.generate_future_token(args.user_id)
        elif args.type == "short":
            token = generator.generate_short_lived_token(args.user_id, seconds=30)
        elif args.type == "replay":
            jti = args.jti or "replay-test-001"
            token = generator.generate_replay_token(jti)
        else:  # custom
            token = generator.generate_token(
                user_id=args.user_id,
                jti=args.jti,
                exp_hours=args.exp_hours,
                nbf_hours=args.nbf_hours
            )
        
        tokens.append(token)
        
        if args.count == 1 or args.show_info:
            generator.print_token_info(token)
        else:
            print(f"Token {i+1}: {token[:50]}...")
    
    # Save to file if specified
    if args.output:
        with open(args.output, "w") as f:
            for token in tokens:
                f.write(token + "\n")
        print(f"\n✅ Tokens saved to {args.output}")
    
    # Print curl command example
    if args.count == 1:
        print("\n💡 Test with curl:")
        print(f"""
curl -X POST http://localhost:8000/validate \\
  -H "Content-Type: application/json" \\
  -d '{{"token": "{tokens[0]}"}}'
        """)


def generate_test_suite():
    """Generate a complete test suite of tokens."""
    print("\n🧪 Generating Test Token Suite...\n")
    
    generator = JWTTokenGenerator()
    
    test_cases = {
        "Valid Token (1h)": generator.generate_valid_token("user123"),
        "Expired Token": generator.generate_expired_token("user456"),
        "Future Token (nbf in 1h)": generator.generate_future_token("user789"),
        "Short-lived (30s)": generator.generate_short_lived_token("user111", 30),
        "Replay Token": generator.generate_replay_token("replay-jti-001"),
        "High Score User": generator.generate_token("testuser1", extra_claims={"info": "high_score"}),
        "Low Score User": generator.generate_token("testuser5", extra_claims={"info": "low_score"}),
    }
    
    # Save to file
    with open("test_tokens.txt", "w") as f:
        for name, token in test_cases.items():
            f.write(f"# {name}\n")
            f.write(f"{token}\n\n")
    
    print("✅ Test tokens generated:")
    for name in test_cases.keys():
        print(f"   - {name}")
    
    print("\n📄 Saved to: test_tokens.txt")
    
    # Print first token as example
    print("\n📋 Example Token (Valid):")
    print("-" * 60)
    print(test_cases["Valid Token (1h)"])
    print("-" * 60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) == 1:
        # No arguments - generate test suite
        generate_test_suite()
    else:
        # Parse CLI arguments
        main()