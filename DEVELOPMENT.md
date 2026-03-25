# Development Guide — Room

Set up your local development environment for the Room application.

---

## Table of Contents

1. [Quick Start (Docker)](#1-quick-start-with-docker-recommended)
2. [Backend Development](#2-backend-development)
3. [Mobile Development](#3-mobile-development)
4. [Database Management](#4-database-management)
5. [Code Style](#5-code-style)

---

## 1. Quick Start with Docker (recommended)

The fastest way to run the full stack locally.

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) ≥ 24
- [Docker Compose](https://docs.docker.com/compose/install/) ≥ 2.20

### Steps

```bash
# 1. Clone the repo
git clone https://github.com/katarymba/room.git
cd room

# 2. Create environment file
cp .env.example .env
# Edit .env if needed (defaults work for local dev)

# 3. Start everything with hot-reload
make up-dev
# or without Makefile:
# docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# 4. The API is available at http://localhost:8000
# Swagger docs: http://localhost:8000/docs
# pgAdmin: http://localhost:5050
```

### Useful `make` commands

```bash
make help          # List all available commands
make up            # Start in production mode (background)
make up-dev        # Start with hot-reload (foreground)
make down          # Stop all services
make logs          # Follow logs for all services
make migrate       # Run database migrations
make test-backend  # Run backend tests
make shell-backend # Open shell in backend container
make shell-db      # Open psql shell
```

---

## 2. Backend Development

### Without Docker

Requirements: Python 3.11+, PostgreSQL 15+ with PostGIS extension.

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — set DATABASE_URL to your local postgres

# Run migrations
alembic upgrade head

# Start the development server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests

```bash
# Inside the backend directory (with venv activated)
pytest -v

# Or via Docker
make test-backend
```

### Adding New Dependencies

```bash
pip install <package>
pip freeze > requirements.txt
```

### Creating Migrations

```bash
# After modifying models in app/models/
alembic revision --autogenerate -m "description of change"
alembic upgrade head
```

---

## 3. Mobile Development

### Prerequisites

- [Node.js](https://nodejs.org/) ≥ 18
- [Expo CLI](https://docs.expo.dev/get-started/installation/)

```bash
npm install -g expo-cli
```

- **Expo Go** app on your phone:
  - [iOS App Store](https://apps.apple.com/app/expo-go/id982107779)
  - [Google Play](https://play.google.com/store/apps/details?id=host.exp.exponent)

### Setup

```bash
cd mobile

# Install dependencies
npm install

# Configure API URL
cp .env.example .env
# Set API_URL to your backend address
```

### Running

```bash
# Start Expo development server
npm start
# or: npx expo start

# Open on physical device
# → Scan the QR code in Expo Go

# Open on iOS simulator (macOS only)
npm run ios

# Open on Android emulator
npm run android
```

### Pointing to your backend

| Scenario | API_URL |
|----------|---------|
| Docker on same machine | `http://localhost:8000` |
| Backend on local network | `http://192.168.1.100:8000` |
| Backend via Tailscale | `http://my-laptop.tail12345.ts.net:8000` |
| Backend via ngrok | `https://abc123.ngrok.io` |

Update `mobile/.env`:

```env
API_URL=http://192.168.1.100:8000
```

### Debugging

- Shake the device to open the Expo developer menu
- Use `console.log` — output appears in the terminal running `npm start`
- Install [React Native Debugger](https://github.com/jhen0409/react-native-debugger) for full Redux/Zustand inspection

---

## 4. Database Management

### View the schema

```bash
# Connect to DB
make shell-db
# or: docker compose exec postgres psql -U room -d room

# List tables
\dt

# Describe a table
\d users

# Quit
\q
```

### Migrations

```bash
# Show migration history
docker compose exec backend alembic history

# Show current version
docker compose exec backend alembic current

# Create a new migration (auto-generated from models)
make migration MSG="add user avatar field"
# or: docker compose exec backend alembic revision --autogenerate -m "add user avatar field"

# Apply migrations
make migrate

# Roll back last migration
docker compose exec backend alembic downgrade -1
```

### Seed data (manual)

```bash
make shell-backend
python -c "from app.database import SessionLocal; ..."
```

### Backup and Restore

```bash
# Backup
docker compose exec -T postgres pg_dump -U room room > backup.sql

# Restore
docker compose exec -T postgres psql -U room room < backup.sql
```

---

## 5. Code Style

### Backend (Python)

We use **black** for formatting and **flake8** for linting.

```bash
# Format code
black app/

# Lint
flake8 app/ --max-line-length=88
```

### Mobile (TypeScript)

We use **ESLint** and **Prettier**.

```bash
# Lint
npm run lint

# Format
npx prettier --write src/
```

---

## Project Structure

```
room/
├── backend/
│   ├── app/
│   │   ├── models/      # SQLAlchemy models
│   │   ├── schemas/     # Pydantic schemas
│   │   ├── routers/     # FastAPI route handlers
│   │   ├── services/    # Business logic
│   │   ├── utils/       # Helpers (security, etc.)
│   │   ├── config.py    # App configuration
│   │   ├── database.py  # DB session setup
│   │   └── main.py      # App entrypoint
│   ├── alembic/         # Database migrations
│   ├── Dockerfile
│   ├── entrypoint.sh
│   └── requirements.txt
├── mobile/
│   ├── src/
│   │   ├── screens/     # App screens
│   │   ├── components/  # Reusable components
│   │   ├── services/    # API, geo, Bluetooth
│   │   ├── store/       # Zustand state
│   │   ├── hooks/       # Custom hooks
│   │   ├── navigation/  # React Navigation
│   │   ├── types/       # TypeScript types
│   │   └── utils/       # Constants, theme
│   └── App.tsx
├── docs/
├── docker-compose.yml
├── docker-compose.dev.yml
├── .env.example
└── Makefile
```
