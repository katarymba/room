# Room — Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Mobile App (Expo)                        │
│                                                                 │
│  Screens ──► Hooks ──► Stores (Zustand) ──► Services (Axios)   │
│                                                  │              │
│                         Location (Expo Location) │              │
│                         Bluetooth (BLE — Phase 3)│              │
└──────────────────────────────────────────────────┼─────────────┘
                                                   │
                                               HTTPS REST API
                                                   │
┌──────────────────────────────────────────────────▼─────────────┐
│                        Backend (FastAPI)                        │
│                                                                 │
│  Routers ──► Services ──► Models ──► Database (PostgreSQL)      │
│  (auth, room, chat, location)                                   │
│                                                                 │
│  Middleware: CORS, JWT auth                                     │
└─────────────────────────────────────────────────────────────────┘
                         │
                ┌────────▼────────┐
                │  PostgreSQL      │
                │  + PostGIS ext   │
                └─────────────────┘
```

## Backend (FastAPI)

### Layer Responsibilities

| Layer      | Directory         | Responsibility                                      |
|------------|-------------------|-----------------------------------------------------|
| Routers    | `app/routers/`    | HTTP endpoints, request validation, response shaping|
| Services   | `app/services/`   | Business logic (auth, geo queries)                  |
| Models     | `app/models/`     | SQLAlchemy ORM models (database schema)             |
| Schemas    | `app/schemas/`    | Pydantic models for request/response validation     |
| Utils      | `app/utils/`      | Pure helpers (password hashing, etc.)               |

### Data Models

```
User
 ├── id: UUID (PK)
 ├── device_id: str (nullable, unique)
 ├── phone: str (nullable, unique)
 ├── phone_verified: bool
 ├── hashed_password: str (nullable)
 ├── location: Geography(POINT) — PostGIS
 ├── location_updated_at: datetime
 ├── is_active: bool
 └── created_at: datetime

Message
 ├── id: UUID (PK)
 ├── user_id: UUID (FK → User)
 ├── text: str (max 500 chars)
 ├── location: Geography(POINT) — where sent
 └── created_at: datetime

Reaction
 ├── id: UUID (PK)
 ├── message_id: UUID (FK → Message)
 ├── user_id: UUID (FK → User)
 ├── reaction_type: str (like, heart, ...)
 └── created_at: datetime

Chat
 ├── id: UUID (PK)
 ├── user1_id: UUID (FK → User)
 ├── user2_id: UUID (FK → User)
 └── created_at: datetime

ChatMessage
 ├── id: UUID (PK)
 ├── chat_id: UUID (FK → Chat)
 ├── sender_id: UUID (FK → User)
 ├── text: str (max 1000 chars)
 └── created_at: datetime
```

### Authentication Flow

1. Mobile calls `/api/auth/register/guest` with device ID  
   → JWT token returned
2. Or mobile calls `/api/auth/register/phone` with phone number  
   → SMS sent; mobile calls `/api/auth/verify/phone` with code  
   → JWT token returned
3. All subsequent requests include `Authorization: Bearer <token>`
4. `get_current_user` dependency validates the token and loads the user

### Geolocation (PostGIS)

- User locations stored as `Geography(POINT, srid=4326)`
- `ST_DWithin` used for radius searches (works with meters on geography type)
- Active users = updated location within last 5 minutes
- Messages anchored to the location where they were sent

## Mobile (React Native / Expo)

### State Management (Zustand)

| Store            | State                                    |
|------------------|------------------------------------------|
| `authStore`      | JWT token, user object, loading flag     |
| `messagesStore`  | Room messages, nearby user count         |

### Navigation

```
Stack Navigator
 ├── Splash       (loading / redirect)
 ├── Auth         (guest or phone login)
 ├── Permissions  (location grant)
 └── Main ──► Bottom Tab Navigator
              ├── Room  (anonymous chat)
              └── Chats (private chats)
```

### Offline Mode (Phase 3)

Bluetooth Low Energy (BLE) will be used when there is no internet.  
The `services/bluetooth.ts` module is a placeholder stub.  
When implemented it will:
1. Advertise the device via BLE
2. Scan for nearby BLE devices
3. Exchange compressed messages over GATT characteristics
4. Automatically switch modes based on connectivity

## Security Considerations

- JWT tokens stored in `expo-secure-store` (hardware-backed on supported devices)
- No user identity information in room messages (truly anonymous)
- Private chats require mutual opt-in (both users must have liked each other)
- All inputs validated by Pydantic on the backend
- Passwords hashed with bcrypt (for phone auth)
- HTTPS required in production (enforce with reverse proxy / load balancer)
