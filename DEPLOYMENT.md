# Deployment Guide — Room

Deploy the Room application to a self-hosted server (e.g., an old laptop) using Docker Compose.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Install Docker & Docker Compose](#1-install-docker--docker-compose)
3. [Clone the Repository](#2-clone-the-repository)
4. [Configure Environment](#3-configure-environment)
5. [Start Services](#4-start-services)
6. [Access Services](#5-access-services)
7. [Network Access Setup](#6-network-access-setup)
8. [Production Considerations](#7-production-considerations)
9. [Troubleshooting](#8-troubleshooting)

---

## Prerequisites

### Hardware

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU      | 2 cores | 4 cores     |
| RAM      | 4 GB    | 8 GB        |
| Disk     | 20 GB   | 50 GB SSD   |

Any laptop from the last 10 years should work fine.

### Software

- **OS:** Ubuntu Server 22.04 LTS (recommended) or any Debian-based distro
- **Network:** Stable internet connection (for remote access) or local WiFi

### Network requirements

- Open port **8000** for the API
- Open port **5050** for pgAdmin (optional, only in trusted networks)

---

## 1. Install Docker & Docker Compose

```bash
# Update package list
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y ca-certificates curl gnupg lsb-release

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Add Docker repository
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
  https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine and Docker Compose plugin
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add current user to the docker group (no sudo needed)
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker compose version
```

---

## 2. Clone the Repository

```bash
git clone https://github.com/katarymba/room.git
cd room
```

---

## 3. Configure Environment

```bash
# Copy the template
cp .env.example .env

# Generate a secure SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"
# Copy the output and paste it as the value of SECRET_KEY in .env

# Edit the configuration
nano .env
```

Minimum values to change in `.env`:

```env
POSTGRES_PASSWORD=your-strong-password
SECRET_KEY=paste-generated-key-here
PGADMIN_DEFAULT_PASSWORD=your-pgadmin-password
```

---

## 4. Start Services

```bash
# Pull images and start all containers in the background
docker compose up -d

# Check that all containers are running
docker compose ps

# Follow logs
docker compose logs -f
```

Expected output from `docker compose ps`:

```
NAME             STATUS
room_postgres    Up (healthy)
room_backend     Up
room_pgadmin     Up
```

---

## 5. Access Services

| Service   | URL                          | Description           |
|-----------|------------------------------|-----------------------|
| API       | http://localhost:8000        | FastAPI application   |
| API Docs  | http://localhost:8000/docs   | Swagger UI            |
| ReDoc     | http://localhost:8000/redoc  | ReDoc documentation   |
| pgAdmin   | http://localhost:5050        | Database management   |

### Configure pgAdmin connection

1. Open http://localhost:5050
2. Log in with `PGADMIN_DEFAULT_EMAIL` and `PGADMIN_DEFAULT_PASSWORD`
3. Right-click **Servers → Register → Server**
4. **General:** Name = `Room`
5. **Connection:**
   - Host: `postgres`
   - Port: `5432`
   - Database: value of `POSTGRES_DB`
   - Username: value of `POSTGRES_USER`
   - Password: value of `POSTGRES_PASSWORD`

---

## 6. Network Access Setup

### 6.1 Local Network Access (same WiFi)

```bash
# Find the server's local IP address
ip addr show | grep "inet " | grep -v 127.0.0.1
# Example output: inet 192.168.1.100/24
```

```bash
# Allow traffic on the API port from your local network
sudo ufw allow from 192.168.1.0/24 to any port 8000
sudo ufw enable
```

From your phone or another device on the same WiFi:

```
http://192.168.1.100:8000
```

Update `mobile/.env`:

```env
API_URL=http://192.168.1.100:8000
```

---

### 6.2 Remote Access — Tailscale (recommended)

Tailscale creates a secure private VPN mesh — free for personal use.

```bash
# Install Tailscale
curl -fsSL https://tailscale.com/install.sh | sh

# Authenticate (opens a browser link)
sudo tailscale up
```

Your server gets a stable Tailscale hostname, e.g. `my-laptop.tail12345.ts.net`.

From any device with Tailscale installed:

```
http://my-laptop.tail12345.ts.net:8000
```

**Benefits:**
- Works from anywhere, even behind NAT
- End-to-end encrypted
- No port forwarding required
- Free for up to 100 devices

---

### 6.3 Remote Access — ngrok (temporary public URL)

Useful for quick demos without a fixed IP.

```bash
# Install ngrok
curl -sSL https://ngrok-agent.s3.amazonaws.com/ngrok.asc \
  | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc > /dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" \
  | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Authenticate (get token at https://dashboard.ngrok.com)
ngrok config add-authtoken YOUR_TOKEN

# Create a public tunnel to the API
ngrok http 8000
```

You get a URL like `https://abc123.ngrok.io` that anyone can access.

> **Note:** The free tier URL changes every time you restart ngrok.

---

## 7. Production Considerations

### 7.1 Reverse Proxy with nginx

```bash
sudo apt install nginx
```

`/etc/nginx/sites-available/room`:

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/room /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

### 7.2 SSL/TLS with Let's Encrypt

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

### 7.3 Automatic Backups

```bash
# /etc/cron.daily/backup-room
#!/bin/bash
BACKUP_DIR=/home/$USER/backups
mkdir -p $BACKUP_DIR
docker compose -f /home/$USER/room/docker-compose.yml exec -T postgres \
  pg_dump -U room room > $BACKUP_DIR/room-$(date +%Y%m%d).sql
# Keep last 7 days
find $BACKUP_DIR -name "room-*.sql" -mtime +7 -delete
```

```bash
sudo chmod +x /etc/cron.daily/backup-room
```

### 7.4 Monitoring

```bash
# Install htop for resource monitoring
sudo apt install htop

# View Docker stats
docker stats
```

### 7.5 Auto-restart on reboot

All services have `restart: unless-stopped` in `docker-compose.yml`, so they
restart automatically when the server reboots.

---

## 8. Troubleshooting

### Container won't start

```bash
# View container logs
docker compose logs backend
docker compose logs postgres
```

### Database connection error

```bash
# Check postgres is healthy
docker compose ps postgres
# Should show: Up (healthy)

# Connect to DB directly
docker compose exec postgres psql -U room -d room
```

### Port already in use

```bash
# Find what's using the port
sudo lsof -i :8000
sudo lsof -i :5432

# Stop the conflicting service
sudo systemctl stop <service-name>
```

### Reset everything (WARNING: deletes all data)

```bash
docker compose down -v --remove-orphans
docker compose up -d
```

### View migration logs

```bash
docker compose exec backend alembic history
docker compose exec backend alembic current
```
