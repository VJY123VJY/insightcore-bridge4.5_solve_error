# InsightBridge v4.0 Architecture

**Version:** 4.0.0  
**Author:** Vijay Dhawan  
**Last Updated:** 2026-01-13

---

## Design Principles

### 1. Fail-Closed Security

**Rule:** When in doubt, DENY.

All components default to the most secure behavior on errors:

- JWT validation error → DENY
- Database connection failure → DENY
- Replay cache error → Treat as replay (DENY)
- Rate limiter error → DENY
- Score lookup failure → Score = 0 (DENY)

**Why:** Prevents security bypasses through induced errors.

---

### 2. Receiver-Side Trust

**Rule:** Never trust JWT payload for enforcement decisions.

**Untrusted:** JWT payload fields (attacker-controlled)  
**Trusted:** Backend database, receiver-controlled services

**Example:**
```python
# ❌ WRONG - Attacker can mint their own score
score = jwt_payload["score"]

# ✅ CORRECT - Score from trusted backend
score = await score_provider.get_score(user_id)
```

---

### 3. Deterministic Behavior

**Rule:** Same input → same output, always.

- No randomness in decision logic
- No hidden state assumptions
- Fully reproducible from logs

---

### 4. Crash Resilience

**Rule:** State must survive restarts.

- Replay cache persisted to database
- Rate limit state persisted
- Scoring state cached with fallback

---

## Component Architecture