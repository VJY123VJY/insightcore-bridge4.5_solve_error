# InsightBridge v4.5 - Installation & Setup Guide

**Last Updated**: January 13, 2026  
**Version**: 4.5.0  
**Status**: Production Ready ✅

---

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Pre-Installation](#pre-installation)
3. [Installation Steps](#installation-steps)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **OS**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: 3.11 or higher
- **RAM**: 512 MB minimum (2 GB recommended)
- **Disk Space**: 500 MB minimum
- **Network**: Internet connection for package downloads

### Recommended Requirements
- **CPU**: 2+ cores
- **RAM**: 4 GB or more
- **Python**: 3.12 or 3.13 (latest stable)
- **OS**: Linux (for production)
- **Database**: PostgreSQL 12+ (for production)

---

## Pre-Installation

### 1. Check Python Version

```bash
python --version
# Should output: Python 3.11.0 or higher
```

If Python is not installed, download from [python.org](https://www.python.org/downloads/)

### 2. Install Git (Optional)

```bash
git --version
# If not installed, download from https://git-scm.com/
```

### 3. Prepare Working Directory

```bash
# Create directory
mkdir -p ~/projects
cd ~/projects

# Or use existing directory
cd /path/to/insightbridge4.5
```

---

## Installation Steps

### Step 1: Extract/Clone Project

```bash
# If you have a zip file
unzip insightbridge4.5.zip
cd insightbridge4.5

# If using git
git clone https://github.com/your-repo/insightbridge.git
cd insightbridge
```

### Step 2: Create Virtual Environment

**Windows:**
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

**macOS/Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

You should see `(.venv)` prefix in your terminal.

### Step 3: Upgrade pip and setuptools

```bash
python -m pip install --upgrade pip setuptools wheel
```

### Step 4: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs all required packages:
- FastAPI & Uvicorn (web framework)
- Pydantic (data validation)
- PyJWT & cryptography (JWT handling)
- SQLAlchemy & asyncpg (database)
- pytest (testing)
- And more...

**Installation should take 2-5 minutes.**

### Step 5: Generate JWT Keys

```bash
python scripts/generate_test_jwts.py
```

This creates:
- `keys/private_key.pem` - RSA private key
- `keys/public_key.pem` - RSA public key
- `test_tokens.txt` - 7 test JWT tokens

**Output Example:**
```
🧪 Generating Test Token Suite...

🔑 Generating new RSA key pair...
✅ Keys generated:
   - keys/private_key.pem
   - keys/public_key.pem
✅ Test tokens generated:
   - Valid Token (1h)
   - Expired Token
   - Future Token (nbf in 1h)
   - Short-lived (30s)
   - Replay Token
   - High Score User
   - Low Score User

📄 Saved to: test_tokens.txt
```

### Step 6: Configure Environment

```bash
# Copy template
cp .env.example .env

# Edit configuration (choose your editor)
nano .env          # Linux/macOS
code .env          # VS Code
notepad .env       # Windows
```

**Key configuration values:**

```env
ENVIRONMENT=development
DEBUG_MODE=false
SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
JWT_PUBLIC_KEY_PATH=./keys/public_key.pem
JWT_PRIVATE_KEY_PATH=./keys/private_key.pem
JWT_ALGORITHM=RS256
JWT_EXPIRATION_HOURS=1
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST_SIZE=120
```

### Step 7: Verify Installation

```bash
# Check Python environment
python --version

# Check installed packages
pip list | grep -E "fastapi|uvicorn|pydantic|pyjwt"

# Check keys exist
ls -la keys/

# Validate configuration
python -c "from app.config import get_settings; settings = get_settings(); print('✅ Config valid')"
```

---

## Configuration

### Development Configuration

For local development, use `.env.example` as template:

```env
ENVIRONMENT=development
DEBUG_MODE=true
LOG_LEVEL=DEBUG
HOST=127.0.0.1
PORT=8000
SECRET_KEY=dev-secret-key-change-in-production
JWT_PUBLIC_KEY_PATH=./keys/public_key.pem
RATE_LIMIT_REQUESTS_PER_MINUTE=1000
```

### Production Configuration

For production deployment:

```env
ENVIRONMENT=production
DEBUG_MODE=false
LOG_LEVEL=WARNING
HOST=0.0.0.0
PORT=8000
SECRET_KEY=<strong-random-key>
JWT_PUBLIC_KEY_PATH=/etc/insightbridge/keys/public_key.pem
DATABASE_URL=postgresql+asyncpg://user:password@db.example.com:5432/insightbridge?ssl=require
REDIS_URL=redis://:password@redis.example.com:6379/0
RATE_LIMIT_REQUESTS_PER_MINUTE=100
RATE_LIMIT_BURST_SIZE=120
TELEMETRY_EMIT_ENABLED=true
```

### Generate Strong Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Example output:
# Drmhze6EPcv0fN_81Bj-nA_7d4hdsI2w3w6dH8twMVw
```

---

## Verification

### 1. Start Development Server

```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Expected output:**
```
INFO:     Will watch for changes in these directories: [...]
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [XXXX] using StatReload
INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
🚀 Starting InsightBridge v4.5.0
   Environment: development
   JWT Algorithm: RS256
✅ Components initialized
INFO:     Application startup complete.
```

### 2. Test Health Endpoint

**In another terminal:**

```bash
curl http://127.0.0.1:8000/health
```

**Expected response:**
```json
{
  "status": "healthy",
  "version": "4.5.0",
  "uptime_seconds": 5,
  "database_connected": true,
  "redis_connected": true,
  "replay_cache_size": 0,
  "timestamp": "2026-01-13T10:30:00"
}
```

### 3. Test Validation Endpoint

```bash
# Get a test token
TOKEN=$(cat test_tokens.txt | grep -A1 "Valid Token" | tail -1)

# Send validation request
curl -X POST http://127.0.0.1:8000/validate \
  -H "Content-Type: application/json" \
  -d "{\"token\": \"$TOKEN\"}"
```

**Expected response:**
```json
{
  "decision": "ALLOW",
  "reason": null,
  "request_id": "...",
  "timestamp": "2026-01-13T10:30:00",
  "score": 95
}
```

### 4. Access API Documentation

Open your browser and visit:
```
http://127.0.0.1:8000/docs
```

You should see the Swagger UI with all endpoints documented.

### 5. Run Tests

```bash
# Install test dependencies (if not already)
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest tests/ -v

# Run with coverage
pytest --cov=app tests/ -v
```

---

## Troubleshooting

### Problem: "ModuleNotFoundError: No module named 'fastapi'"

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt

# Or install specific package
pip install fastapi uvicorn
```

### Problem: "JWT public key not found"

**Solution:**
```bash
# Regenerate keys
python scripts/generate_test_jwts.py

# Verify keys exist
ls -la keys/
```

### Problem: "Port 8000 already in use"

**Solution:**
```bash
# Use different port
python -m uvicorn app.main:app --port 8001

# Or find and kill process using port 8000
# Linux/macOS:
lsof -i :8000
kill -9 <PID>

# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F
```

### Problem: "Permission denied" on keys

**Solution:**
```bash
# Fix key permissions (Linux/macOS)
chmod 600 keys/private_key.pem
chmod 644 keys/public_key.pem
```

### Problem: "Config validation error"

**Solution:**
```bash
# Check config validity
python -c "from app.config import get_settings; get_settings()"

# View all settings
python -c "from app.config import get_settings; import json; print(json.dumps(get_settings().dict(), indent=2, default=str))"
```

### Problem: Virtual environment not activated

**Solution:**
```bash
# Windows - Reactivate:
.\.venv\Scripts\Activate.ps1

# macOS/Linux - Reactivate:
source .venv/bin/activate

# Should show (.venv) prefix in terminal
```

### Problem: Tests failing

**Solution:**
```bash
# Verify environment
python -m pytest --version

# Run with verbose output
pytest tests/ -vv

# Run specific test file
pytest tests/unit/test_jwt_validator.py -v

# Check what's being tested
pytest tests/ --collect-only
```

---

## Next Steps

1. ✅ **Installation Complete**
2. 📖 **Read Documentation**
   - `README.md` - Full project guide
   - `docs/SECURITY_GUIDE.md` - Security best practices
   - `DOCUMENTATION.html` - Complete HTML documentation
3. 🧪 **Run Tests**
   - `pytest tests/ -v`
4. 🚀 **Deploy**
   - For development: Already running on localhost:8000
   - For production: See Production Deployment section in README.md
5. 📊 **Monitor**
   - Check health: `curl http://localhost:8000/health`
   - View metrics: `curl http://localhost:8000/metrics`
   - Review logs in console

---

## Support

For issues or questions:

1. **Check this guide** - Most common issues are covered above
2. **Review documentation** - See `docs/` folder
3. **Check logs** - Look at console output for error messages
4. **Run tests** - `pytest -v` to identify issues
5. **Verify configuration** - Ensure `.env` is properly set

---

## Installation Complete! ✅

Your InsightBridge v4.5 installation is ready. The server is running and all endpoints are operational.

**Quick Commands:**
- Start server: `python -m uvicorn app.main:app --reload`
- Run tests: `pytest -v`
- View docs: http://localhost:8000/docs
- Generate tokens: `python scripts/generate_test_jwts.py`

**Version**: 4.5.0  
**Date**: January 13, 2026  
**Status**: ✅ Ready for Production
