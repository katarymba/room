# Security Guide

This document describes the security measures implemented in the Room backend.

## Secret Management

### SECRET_KEY
- **Required**: Must be set to a non-default value in production
- **Minimum length**: 32 characters
- **Generation**: `python -c "import secrets; print(secrets.token_hex(32))"`
- Weak values (e.g. `changeme`, `admin`, `secret`) are rejected at startup
- The app **will not start** with a weak `SECRET_KEY` when `DEBUG=False`

### POSTGRES_PASSWORD
- **Minimum length**: 16 characters in production
- Weak values are rejected at startup when `DEBUG=False`

## JWT Authentication

### Access Token
- Lifetime: **30 minutes** (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- Passed via HTTP header: `Authorization: Bearer <token>`
- **Never passed in URL query parameters**

### Refresh Token
- Lifetime: **30 days** (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)
- Stored in the `refresh_tokens` database table (hashed opaque token)
- Endpoint: `POST /api/auth/refresh` — exchange refresh token for a new access token (token rotation)
- Revoked on logout: `POST /api/auth/logout`
- Revoke all sessions: `POST /api/auth/logout/all`

## WebSocket Security

WebSocket connections **require message-based authentication**:

1. Client connects to `/ws/room` (no token in the URL)
2. Server immediately sends `{"type": "auth_required"}`
3. Client must send within **5 seconds**:
   ```json
   {"type": "auth", "token": "<jwt>"}
   ```
4. Server responds with `{"type": "auth_success"}` or closes with code `4001`

Connections are closed immediately on:
- Authentication timeout (5 seconds)
- Invalid/expired JWT token
- Malformed JSON

## Rate Limiting

### Short-window limits (DoS / spam protection, all users)

| Action | Limit |
|--------|-------|
| Messages | 5 per 10 seconds |
| Reactions | 10 per 10 seconds |
| Login/verify attempts | 5 per minute (per IP) |

### Tier-based limits

| Action | Free tier | Premium tier |
|--------|-----------|-------------|
| Messages | 20 per day | Unlimited |
| Reactions | 100 per hour | 1,000 per hour |
| Connections | 10 per hour | 100 per hour |

Exceeded limits return HTTP **429 Too Many Requests**.

## Anti-Spam

- **Duplicate message detection**: identical messages from the same user within 1 minute are rejected with HTTP 429
- Messages are validated: non-empty, stripped of leading/trailing whitespace, maximum 500 characters

## Input Validation

All inputs are validated using Pydantic schemas:

- **Coordinates**: `-90 ≤ latitude ≤ 90`, `-180 ≤ longitude ≤ 180`
- **Messages**: non-empty, max 500 characters
- **Phone numbers**: international format validated by regex
- **Radius**: 10–200 meters

## CORS

In production, restrict `CORS_ORIGINS` in your `.env` file to your actual frontend origins:

```env
CORS_ORIGINS=["https://yourapp.com"]
```

Allowed methods: `GET, POST, PUT, DELETE, OPTIONS`  
Allowed headers: `Authorization, Content-Type, Accept`

## HTTPS / WSS

In production:
- Configure Nginx (or another reverse proxy) to terminate SSL/TLS
- Redirect all HTTP traffic to HTTPS
- WebSocket connections will automatically use WSS when behind an HTTPS reverse proxy

See `DEPLOYMENT.md` for Nginx configuration examples.

## Redis

Redis is used for:
- Rate limiting (planned upgrade from in-memory)
- WebSocket pub/sub for horizontal scaling (future)
- Cache for frequently requested data (future)

Configure via `REDIS_URL` environment variable.

## Logging

The backend uses structured JSON logging. The following events are logged:

- All HTTP 4xx and 5xx responses (warning level)
- Authentication failures
- Rate limit violations
- WebSocket connection/disconnection events

Set `LOG_LEVEL` environment variable to control verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`).

## Health Check

```
GET /health
```

Returns `{"status": "healthy", "version": "..."}` — used by Docker health checks and monitoring.

## Reporting Vulnerabilities

If you discover a security vulnerability, please report it privately to the repository maintainers rather than opening a public issue.
