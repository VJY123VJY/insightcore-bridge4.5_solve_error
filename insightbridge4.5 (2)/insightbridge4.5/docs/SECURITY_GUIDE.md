# InsightBridge Security Configuration Guide

## Overview

This guide provides best practices for securing InsightBridge v4.5, including JWT token generation, configuration management, and production deployment recommendations.

## Table of Contents

1. [Quick Start](#quick-start)
2. [JWT Token Generation](#jwt-token-generation)
3. [Configuration Security](#configuration-security)
4. [Environment Setup](#environment-setup)
5. [Production Deployment](#production-deployment)
6. [Security Best Practices](#security-best-practices)

---

## Quick Start

### Generate JWT Keys and Tokens

```bash
# Generate RSA key pair and test tokens
python scripts/generate_test_jwts.py

# Generate specific token types
python scripts/generate_test_jwts.py --type valid --user-id alice --count 1

# Generate custom tokens with specific claims
python scripts/generate_test_jwts.py --type custom --user-id bob --exp-hours 24 --show-info
```

This creates:
- `keys/private_key.pem` - Private RSA key (keep secure!)
- `keys/public_key.pem` - Public RSA key (safe to share)
- `test_tokens.txt` - Test tokens for development

---

## JWT Token Generation

### Token Types

The `generate_test_jwts.py` script supports multiple token scenarios:

| Type | Use Case | Expiry |
|------|----------|--------|
| `valid` | Normal authentication | 1 hour |
| `expired` | Test expired token handling | Already expired |
| `future` | Test nbf validation | Valid in 1 hour |
| `short` | Test short-lived tokens | 30 seconds |
| `replay` | Test replay attack detection | 1 hour (same JTI) |
| `custom` | Custom expiry and claims | Configurable |

### JWT Structure

All tokens are signed with RS256 (RSA 2048-bit) by default:

```
Header.Payload.Signature
```

**Header:**
```json
{
  "alg": "RS256",
  "typ": "JWT"
}
```

**Payload (Example):**
```json
{
  "sub": "user123",
  "jti": "unique-jwt-id",
  "iat": 1768280581,
  "nbf": 1768280581,
  "exp": 1768284181
}
```

### CLI Examples

```bash
# Generate valid token for user 'alice'
python scripts/generate_test_jwts.py --type valid --user-id alice --show-info

# Generate 5 expired tokens
python scripts/generate_test_jwts.py --type expired --count 5 --output expired_tokens.txt

# Generate custom token valid for 24 hours
python scripts/generate_test_jwts.py --type custom --exp-hours 24 --user-id service_account

# Generate replay token (same JTI for multiple uses)
python scripts/generate_test_jwts.py --type replay --jti "replay-001" --show-info

# Decode token without verification
python -c "
import jwt
token = '<your-token-here>'
print(jwt.decode(token, options={'verify_signature': False}))
"
```

---

## Configuration Security

### Environment Variables

All sensitive configuration uses environment variables. **Never hardcode secrets!**

Create a `.env` file (add to `.gitignore`):

```bash
# Copy the template
cp .env.example .env

# Edit with your values
nano .env
```

### Critical Security Settings

#### 1. Application Secret Key

```bash
# Generate a strong secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Add to .env
SECRET_KEY=your-generated-key-here
```

#### 2. JWT Configuration

**For RSA (Recommended):**
```env
JWT_ALGORITHM=RS256
JWT_PUBLIC_KEY_PATH=./keys/public_key.pem
JWT_PRIVATE_KEY_PATH=./keys/private_key.pem
JWT_EXPIRATION_HOURS=1
```

**For HMAC (Symmetric):**
```env
JWT_ALGORITHM=HS256
JWT_SECRET_KEY=your-hmac-secret-key
```

#### 3. Database Configuration

```env
# Development (local)
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/insightbridge

# Production (with SSL)
DATABASE_URL=postgresql+asyncpg://user:strong_password@db.prod.com:5432/insightbridge?ssl=require
DB_SSL_MODE=require
```

#### 4. Redis Cache

```env
# Development (no auth)
REDIS_URL=redis://localhost:6379/0

# Production (with auth and SSL)
REDIS_URL=redis://:password@redis.prod.com:6379/0
REDIS_SSL=true
```

#### 5. Third-party API Keys

```env
SCORE_API_KEY=sk_live_your_real_key_here
```

### Configuration Validation

The application validates configuration on startup:

```python
from app.config import get_settings

settings = get_settings()

# Automatic validation for production
if settings.is_production():
    # Validates required fields
    # Ensures strong secrets
    # Checks SSL configurations
    pass
```

---

## Environment Setup

### Development Environment

```bash
# 1. Create virtual environment
python -m venv .venv

# 2. Activate (Windows)
.venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt

# 4. Generate JWT keys
python scripts/generate_test_jwts.py

# 5. Create .env file
cp .env.example .env
```

### Environment Validation

```bash
# Check Python environment
python --version

# Verify JWT keys exist
ls -la keys/

# Test JWT generation
python scripts/generate_test_jwts.py --type valid --show-info
```

---

## Production Deployment

### Pre-deployment Checklist

- [ ] Generate new RSA key pair (don't use development keys!)
- [ ] Set all required environment variables
- [ ] Enable `DEBUG_MODE=false`
- [ ] Set `ENVIRONMENT=production`
- [ ] Configure SSL/TLS for all services
- [ ] Set strong database passwords
- [ ] Enable Redis authentication
- [ ] Configure rate limiting appropriately
- [ ] Set up monitoring and alerting

### Secure Key Management

**Private Key Protection:**

```bash
# Generate production key pair
python scripts/generate_test_jwts.py

# Secure permissions (Linux/Mac)
chmod 600 keys/private_key.pem

# Store in secret management system
# - AWS Secrets Manager
# - HashiCorp Vault
# - Azure Key Vault
# - GitHub Secrets (for CI/CD)
```

### Production Configuration Example

```env
# Application
ENVIRONMENT=production
DEBUG_MODE=false
SECRET_KEY=<generated-strong-key>

# Server
HOST=0.0.0.0
PORT=8000

# JWT
JWT_ALGORITHM=RS256
JWT_EXPIRATION_HOURS=1
JWT_CLOCK_DRIFT_SECONDS=30

# Database
DATABASE_URL=postgresql+asyncpg://produser:${DB_PASSWORD}@db.prod.internal:5432/insightbridge?ssl=require
DB_SSL_MODE=require
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Redis
REDIS_URL=redis://:${REDIS_PASSWORD}@redis.prod.internal:6379/0
REDIS_SSL=true

# Rate Limiting
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST_SIZE=120

# Telemetry
TELEMETRY_EMIT_ENABLED=true
```

---

## Security Best Practices

### 1. Secret Management

- ✅ Use environment variables for all secrets
- ✅ Rotate secrets regularly
- ✅ Use strong, randomly generated values
- ❌ Never commit `.env` files
- ❌ Never log sensitive values
- ❌ Never hardcode credentials

### 2. JWT Security

- ✅ Use RS256 (RSA) for asymmetric signing
- ✅ Validate token signature before use
- ✅ Check expiration (`exp` claim)
- ✅ Check not-before time (`nbf` claim)
- ✅ Use unique JWT IDs (`jti` claim) for replay prevention
- ✅ Include user ID in `sub` claim
- ❌ Don't trust tokens without verification
- ❌ Don't log full tokens
- ❌ Don't store tokens in plain text

### 3. Database Security

- ✅ Use strong passwords (25+ characters, mixed case, numbers, symbols)
- ✅ Enable SSL/TLS for database connections
- ✅ Use connection pooling
- ✅ Implement SQL injection prevention (use ORM)
- ✅ Encrypt sensitive data at rest
- ✅ Limit database user permissions
- ❌ Don't use default credentials
- ❌ Don't expose database URLs in logs

### 4. API Security

- ✅ Require HTTPS only in production
- ✅ Implement rate limiting
- ✅ Validate all input
- ✅ Implement CORS properly
- ✅ Use security headers (HSTS, CSP, X-Frame-Options)
- ✅ Implement request signing for sensitive operations
- ❌ Don't expose sensitive error messages
- ❌ Don't allow unauthenticated access

### 5. Monitoring & Logging

- ✅ Log authentication attempts
- ✅ Log authorization failures
- ✅ Monitor for suspicious patterns
- ✅ Alert on security events
- ✅ Audit sensitive operations
- ❌ Don't log passwords
- ❌ Don't log full tokens
- ❌ Don't log API keys

### 6. Code Security

- ✅ Keep dependencies up to date
- ✅ Run security scanners (bandit, safety)
- ✅ Code review security-critical code
- ✅ Use type hints for API validation
- ✅ Implement proper error handling
- ❌ Don't ignore security warnings
- ❌ Don't use eval() or exec()
- ❌ Don't suppress exceptions silently

---

## Testing Security

### Test Valid Token

```bash
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -d '{"token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."}'
```

### Test Expired Token

```bash
python scripts/generate_test_jwts.py --type expired --show-info
```

### Test Replay Prevention

```bash
# Generate replay token
python scripts/generate_test_jwts.py --type replay --jti "test-001" --show-info

# Use it twice - second should fail
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -d '{"token": "..."}'
```

---

## Troubleshooting

### Issue: "JWT_SECRET_KEY must be set for HMAC algorithms"

**Solution:** Either use RS256 with RSA keys or set JWT_SECRET_KEY:
```env
JWT_ALGORITHM=HS256
JWT_SECRET_KEY=your-hmac-secret
```

### Issue: "Private key not found"

**Solution:** Generate keys first:
```bash
python scripts/generate_test_jwts.py
```

### Issue: "Token verification failed"

**Solution:** Ensure public key path is correct:
```env
JWT_PUBLIC_KEY_PATH=./keys/public_key.pem
```

### Issue: Production validation errors

**Solution:** Check all required fields in .env:
```bash
python -c "from app.config import get_settings; get_settings()"
```

---

## Additional Resources

- [RFC 7519 - JWT Specification](https://tools.ietf.org/html/rfc7519)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [OWASP API Security Top 10](https://owasp.org/www-project-api-security/)
- [FastAPI Security Documentation](https://fastapi.tiangolo.com/tutorial/security/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)

---

## Support

For security issues or questions:
1. Check this guide first
2. Review code comments
3. Run the test suite
4. Consult the logs

For vulnerabilities, please report privately to the security team.
