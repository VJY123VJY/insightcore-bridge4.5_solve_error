# JWT & Config Security - Quick Reference

## 🔑 Generate Tokens

```bash
# Test suite (7 tokens)
python scripts/generate_test_jwts.py

# Valid token (1 hour)
python scripts/generate_test_jwts.py --type valid --user-id alice

# Expired token
python scripts/generate_test_jwts.py --type expired

# Custom expiry (24 hours)
python scripts/generate_test_jwts.py --type custom --exp-hours 24 --show-info

# Multiple tokens to file
python scripts/generate_test_jwts.py --type valid --count 10 --output tokens.txt
```

## 🔐 Configure Environment

```bash
# 1. Copy template
cp .env.example .env

# 2. Edit values
nano .env

# 3. Generate secret key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 4. Validate
python -c "from app.config import get_settings; print('✅ Config valid')"
```

## 📋 Key Variables

| Variable | Value | Notes |
|----------|-------|-------|
| `ENVIRONMENT` | development, staging, production | - |
| `SECRET_KEY` | 32+ random chars | Use secrets module |
| `JWT_ALGORITHM` | RS256 (default) | RS256, HS256, etc. |
| `JWT_EXPIRATION_HOURS` | 1 | Token lifetime |
| `DATABASE_URL` | postgresql://user:pass@host:port/db | - |
| `REDIS_URL` | redis://host:6379/0 | - |

## 🧪 Test Tokens

```bash
# View test tokens
cat test_tokens.txt

# Decode token (no verification)
python -c "import jwt; print(jwt.decode('TOKEN', options={'verify_signature': False}))"

# Use with curl
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -d '{"token": "TOKEN"}'
```

## 📁 Files Created

```
keys/
  ├── private_key.pem (1.7 KB) - KEEP SECURE!
  └── public_key.pem (451 B)   - Safe to share

.env.example                   - Configuration template
app/config.py                  - Enhanced config with validators
test_tokens.txt               - 7 test JWT tokens
docs/SECURITY_GUIDE.md        - Full security guide
SETUP_COMPLETE.md             - Setup summary
```

## ⚡ Common Commands

```bash
# Generate keys only
python scripts/generate_test_jwts.py

# Get single token with info
python scripts/generate_test_jwts.py --type valid --user-id test --show-info

# Generate 100 tokens
python scripts/generate_test_jwts.py --type valid --count 100 --output bulk_tokens.txt

# Test replay detection
python scripts/generate_test_jwts.py --type replay --jti "same-id"
```

## 🛡️ Security Checklist

- [ ] Keys generated in `keys/` directory
- [ ] `.env` created from `.env.example`
- [ ] `SECRET_KEY` set to strong random value
- [ ] `DATABASE_URL` configured
- [ ] `REDIS_URL` configured
- [ ] `ENVIRONMENT` set correctly
- [ ] Config validates: `python -c "from app.config import get_settings; get_settings()"`
- [ ] Test tokens in `test_tokens.txt`

## 📚 More Info

- Full guide: `docs/SECURITY_GUIDE.md`
- Setup summary: `SETUP_COMPLETE.md`
- This reference: `JWT_CONFIG_REFERENCE.md`

## 🚀 Go Live Checklist

- [ ] Use `ENVIRONMENT=production`
- [ ] Generate NEW production keys
- [ ] Set strong `SECRET_KEY`
- [ ] Enable database SSL: `DB_SSL_MODE=require`
- [ ] Enable Redis auth: `REDIS_URL=redis://:password@host:port/0`
- [ ] Set `DEBUG_MODE=false`
- [ ] Configure rate limiting
- [ ] Enable monitoring/logging
- [ ] Run security audit: `bandit -r app/`

## ⚠️ Important

- **NEVER commit `.env` file**
- **NEVER share private keys**
- **NEVER use dev keys in production**
- **ALWAYS rotate secrets regularly**
- **ALWAYS use HTTPS in production**

---

Created: 2026-01-13  
Version: InsightBridge v4.5  
Status: ✅ Ready for Development
