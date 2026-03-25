# Room Backend (FastAPI)

Backend API for the Room anonymous chat application.

## Tech Stack

- **Framework:** FastAPI
- **Database:** PostgreSQL
- **ORM:** SQLAlchemy
- **Authentication:** JWT
- **Geolocation:** PostGIS

## Database Schema

### Core Entities

**User**
- id (UUID)
- device_id / phone
- created_at
- last_location (Point)

**Message**
- id (UUID)
- user_id (FK)
- text
- location (Point - lat/lng)
- timestamp
- room_radius (default: 200m)

**Reaction**
- id (UUID)
- message_id (FK)
- user_id (FK)
- type (like, etc.)
- created_at

**Chat**
- id (UUID)
- user1_id (FK)
- user2_id (FK)
- created_at
- is_active

**ChatMessage**
- id (UUID)
- chat_id (FK)
- sender_id (FK)
- text
- timestamp

## API Endpoints

### Authentication
- `POST /auth/register` - Register user (phone/guest)
- `POST /auth/login` - Login
- `POST /auth/verify` - Verify SMS code

### Room
- `GET /room/nearby` - Get users count nearby
- `GET /room/messages` - Get messages in radius
- `POST /room/messages` - Send message to room

### Reactions
- `POST /messages/{id}/reactions` - React to message
- `GET /messages/{id}/reactions` - Get message reactions

### Chats
- `GET /chats` - Get user's chats
- `POST /chats` - Create private chat (if mutual match)
- `GET /chats/{id}/messages` - Get chat messages
- `POST /chats/{id}/messages` - Send message to chat

### Location
- `POST /location/update` - Update user location

## Installation

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Configuration

Create `.env` file:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/room
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Run

```bash
uvicorn app.main:app --reload
```

API docs available at: `http://localhost:8000/docs`

## Development

```bash
# Run migrations
alembic upgrade head

# Create new migration
alembic revision --autogenerate -m "description"

# Run tests
pytest
```