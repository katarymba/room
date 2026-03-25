# Room — Setup Instructions

## Prerequisites

| Tool              | Version       | Notes                          |
|-------------------|---------------|--------------------------------|
| Python            | 3.11+         | Backend                        |
| PostgreSQL        | 14+           | With PostGIS extension         |
| Node.js           | 18+           | Mobile app                     |
| npm               | 9+            | Package manager                |
| Expo CLI          | latest        | `npm i -g expo-cli`            |

---

## Backend Setup

### 1. Create and activate virtual environment

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up PostgreSQL with PostGIS

```sql
-- Run as postgres superuser
CREATE USER room_user WITH PASSWORD 'room_pass';
CREATE DATABASE room_db OWNER room_user;
\c room_db
CREATE EXTENSION IF NOT EXISTS postgis;
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env with your database URL, secret key, etc.
```

### 5. Run database migrations

```bash
alembic upgrade head
```

### 6. Start the development server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs available at: http://localhost:8000/docs

---

## Mobile App Setup

### 1. Install dependencies

```bash
cd mobile
npm install
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit EXPO_PUBLIC_API_URL to point to your backend
```

For local development:
- iOS Simulator: use `http://localhost:8000/api`
- Android Emulator: use `http://10.0.2.2:8000/api`
- Physical device: use your machine's local IP, e.g. `http://192.168.1.x:8000/api`

### 3. Start the app

```bash
npm start
# Then press 'i' for iOS, 'a' for Android, or scan QR with Expo Go
```

---

## Running with Docker (optional)

A `docker-compose.yml` can be added later. For now, run services manually.

---

## Creating Database Migrations

After modifying SQLAlchemy models:

```bash
# Auto-generate migration
alembic revision --autogenerate -m "description of change"

# Review the generated file in alembic/versions/
# Then apply:
alembic upgrade head
```

---

## Environment Variables Reference

### Backend (`backend/.env`)

| Variable                       | Description                                          | Default                                              |
|-------------------------------|------------------------------------------------------|------------------------------------------------------|
| `DATABASE_URL`                | PostgreSQL connection string                         | `postgresql://room_user:room_pass@localhost/room_db` |
| `SECRET_KEY`                  | JWT signing secret (use long random string)          | _(change in production)_                             |
| `ALGORITHM`                   | JWT algorithm                                        | `HS256`                                              |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime                                       | `10080` (7 days)                                     |
| `DEBUG`                       | Enable debug mode                                    | `False`                                              |
| `CORS_ORIGINS`                | Allowed CORS origins (JSON list)                     | `["*"]`                                              |
| `DEFAULT_RADIUS_METERS`       | Default room radius                                  | `100`                                                |
| `MAX_RADIUS_METERS`           | Maximum room radius                                  | `200`                                                |

### Mobile (`mobile/.env`)

| Variable               | Description          | Default                     |
|-----------------------|----------------------|-----------------------------|
| `EXPO_PUBLIC_API_URL` | Backend API base URL | `http://localhost:8000/api` |

---

## Running Tests

### Backend

```bash
cd backend
pytest
```

### Mobile (type checking)

```bash
cd mobile
npm run type-check
npm run lint
```
