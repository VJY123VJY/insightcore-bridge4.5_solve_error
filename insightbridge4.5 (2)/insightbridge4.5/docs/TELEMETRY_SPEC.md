# Telemetry Specification v1.0.0

**Last Updated:** 2026-01-13  
**Owner:** Vijay Dhawan  
**Status:** Production

---

## Overview

This document defines the telemetry contract for InsightBridge v4.0. All telemetry events follow this schema to ensure machine-readable, consistent logging.

---

## Event Types

### 1. `gateway.decision.made`

Emitted when a validation decision is made.

**Fields:**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `version` | string | Schema version | `"1.0.0"` |
| `event_type` | string | Event type identifier | `"gateway.decision.made"` |
| `request_id` | string | Unique request UUID | `"a1b2c3d4-..."` |
| `timestamp` | ISO8601 | Event timestamp (UTC) | `"2026-01-13T10:30:00Z"` |
| `decision` | enum | `ALLOW`, `DENY`, `MONITOR` | `"ALLOW"` |
| `reason` | enum | Deny reason (null if ALLOW) | `"EXPIRED_TOKEN"` |
| `score` | integer | User trust score (0-100) | `75` |
| `user_id_hash` | string | SHA256 hash of user ID | `"a3f5..."` |
| `latency_ms` | integer | Request latency in milliseconds | `45` |

**Example:**
```json
{
  "version": "1.0.0",
  "event_type": "gateway.decision.made",
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "timestamp": "2026-01-13T10:30:00Z",
  "decision": "ALLOW",
  "reason": null,
  "score": 75,
  "user_id_hash": "a3f5b2c1...",
  "latency_ms": 45
}
```

---

### 2. `gateway.error`

Emitted when an error occurs.

**Fields:**

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `version` | string | Schema version | `"1.0.0"` |
| `event_type` | string | Event type identifier | `"gateway.error"` |
| `request_id` | string | Unique request UUID | `"a1b2c3d4-..."` |
| `timestamp` | ISO8601 | Event timestamp (UTC) | `"2026-01-13T10:30:00Z"` |
| `error_type` | string | Error class name | `"DatabaseConnectionError"` |
| `error_message` | string | Sanitized error message | `"Connection timeout"` |

**Example:**
```json
{
  "version": "1.0.0",
  "event_type": "gateway.error",
  "request_id": "123e4567-e89b-12d3-a456-426614174000",
  "timestamp": "2026-01-13T10:30:00Z",
  "error_type": "DatabaseConnectionError",
  "error_message": "Connection timeout after 5s"
}
```

---

## Field Rules

### Privacy & Security

- ✅ **NO JWT contents in logs** - Never log token strings
- ✅ **NO plaintext user IDs** - Always hash with SHA256
- ✅ **NO IP addresses** - Or anonymize last octet
- ✅ **NO secrets** - No API keys, passwords, tokens

### Format Standards

- ✅ **All timestamps in UTC ISO8601** - `YYYY-MM-DDTHH:MM:SSZ`
- ✅ **All durations in milliseconds** - Integer values
- ✅ **All enums in UPPER_CASE** - Consistent casing

---

## Versioning & Breaking Changes

### Version Format

`MAJOR.MINOR.PATCH` (Semantic Versioning)

- **MAJOR**: Breaking changes (field removals, type changes)
- **MINOR**: New fields added (backward compatible)
- **PATCH**: Documentation fixes, clarifications

### Breaking Change Process

1. **Announce** deprecation 30 days in advance
2. **Dual-write** old and new format during transition
3. **Increment** major version
4. **Document** migration guide

---

## Deny Reasons Enum

| Value | Description |
|-------|-------------|
| `EXPIRED_TOKEN` | JWT has expired |
| `NOT_YET_VALID` | JWT nbf in future |
| `REPLAY_DETECTED` | JWT ID seen before |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `INVALID_SIGNATURE` | JWT signature invalid |
| `LOW_SCORE` | User score below threshold |
| `MALFORMED_TOKEN` | JWT parsing failed |
| `INTERNAL_ERROR` | System error occurred |

---

## Consumers

### InsightFlow Team

**Use Case:** Real-time analytics dashboard  
**Fields Used:** `decision`, `score`, `latency_ms`, `timestamp`  
**SLA:** 99.9% schema compliance

### Security Operations

**Use Case:** Incident response  
**Fields Used:** All fields  
**SLA:** 100% retention for 90 days

---

## Change Log

### v1.0.0 (2026-01-13)
- Initial production release
- Defined core event types
- Established privacy rules