# Security Guide

This document describes the security measures implemented in Room and provides guidance for production deployments.

---

## Authentication

### Access Tokens (JWT)

- **Lifetime**: 30 minutes (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
- **Algorithm**: HS256
- **Transport**: HTTP `Authorization: Bearer <token>` header only — tokens are **never** passed in URLs

### Refresh Tokens

- **Lifetime**: 30 days (configurable via `REFRESH_TOKEN_EXPIRE_DAYS`)
- **Storage**: Stored in the `refresh_tokens` database table
- **Rotation**: Each use of `/auth/refresh` issues a new refresh token and revokes the old one
- **Revocation**: Use `POST /auth/logout` to immediately invalidate a refresh token

#### Refresh token flow

```
1. Client calls POST /auth/register/guest  →  receives {access_token, refresh_token}
2. Access token expires after 30 minutes
3. Client calls POST /auth/refresh  {refresh_token: "..."}
   →  receives new {access_token, refresh_token}  (old token revoked)
4. On logout: POST /auth/logout  {refresh_token: "..."}
   →  token is revoked, user must re-authenticate
```

### WebSocket Authentication

WebSocket connections use **message-based authentication** (no token in the URL):

```
1. Client connects to /ws/room  (no token in URL)
2. Server sends {"type": "auth_required"}
3. Client sends {"type": "auth", "token": "<access_token>"}  within 5 seconds
4. Server replies {"type": "auth_success"} or closes with code 4001
```

---

## Secret Management

### Requirements

| Secret | Minimum | Validation |
|--------|---------|------------|
| `SECRET_KEY` | 32 characters | App refuses to start if too short or default value |
| `POSTGRES_PASSWORD` | 16 characters | App refuses to start with weak passwords (changeme, admin, etc.) |

### Generating Secrets

```bash
# SECRET_KEY
python -c "import secrets; print(secrets.token_hex(32))"

# POSTGRES_PASSWORD
python -c "import secrets; print(secrets.token_urlsafe(24))"
```

The application **will not start** in production (`DEBUG=False`) with:
- `SECRET_KEY` shorter than 32 characters
- `SECRET_KEY` equal to the default placeholder
- `POSTGRES_PASSWORD` shorter than 16 characters
- `POSTGRES_PASSWORD` in the list of known weak values

---

## Rate Limiting

### Short-window (anti-spam)

| Action | Limit |
|--------|-------|
| Messages | 5 per 10 seconds |
| Reactions | 10 per 10 seconds |
| Login attempts | 5 per minute (per phone) |

### Per-user quotas

| Tier | Messages | Reactions | Connections |
|------|----------|-----------|-------------|
| Free | 20/day | 100/hour | 10/hour |
| Premium | Unlimited | 1000/hour | 100/hour |

Rate limit violations return **HTTP 429 Too Many Requests**.

### Redis-backed Rate Limiting (Production)

Set `REDIS_URL` to enable Redis-backed rate limiting, which works correctly across multiple backend instances.

---

## CORS

In production, replace wildcard origins with explicit allowed domains:

```env
CORS_ORIGINS=["https://your-app.example.com"]
```

Allowed HTTP methods: `GET, POST, PUT, DELETE`  
Allowed headers: `Authorization, Content-Type`

---

## HTTPS / WSS

**Always use HTTPS in production.** WebSocket connections should use `wss://`.

### Nginx SSL configuration example

```nginx
server {
    listen 443 ssl;
    server_name your-app.example.com;

    ssl_certificate     /etc/letsencrypt/live/your-app.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-app.example.com/privkey.pem;

    location / {
        proxy_pass http://localhost:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Redirect HTTP → HTTPS
server {
    listen 80;
    server_name your-app.example.com;
    return 301 https://$host$request_uri;
}
```

---

## Data Validation

All user input is validated via Pydantic schemas:

- **Message text**: 1–500 characters, whitespace-only messages rejected
- **Coordinates**: latitude −90 to 90, longitude −180 to 180
- **Phone numbers**: international format validation

---

## Logging

The application uses structured JSON logging. All HTTP requests are logged with:
- HTTP method and path
- Response status code
- Request duration (ms)

All 4xx and 5xx responses are logged at `WARNING` level. Logs include authentication failures and rate limit violations.

### Log rotation

Configure your deployment to rotate logs:

```bash
# /etc/logrotate.d/room
/var/log/room/*.log {
    daily
    rotate 14
    compress
    missingok
    notifempty
}
```

---

## Database Backups

Schedule daily backups with at least 7 days retention:

```bash
#!/bin/bash
# backup.sh — run via cron: 0 3 * * * /opt/room/backup.sh
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=/backups/room
mkdir -p "$BACKUP_DIR"
docker exec room_postgres pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" \
    | gzip > "$BACKUP_DIR/room_$DATE.sql.gz"
# Remove backups older than 7 days
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +7 -delete
```

---

## Health Check

The `/health` endpoint returns `200 OK` when the service is running:

```bash
curl https://your-app.example.com/health
# {"status": "healthy", "version": "0.1.0"}
```

Use this endpoint with your load balancer or uptime monitoring.
