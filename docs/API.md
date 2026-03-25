# Room API Documentation

Base URL: `http://localhost:8000/api`

## Authentication

All endpoints except `/auth/*` require a `Bearer` token in the `Authorization` header.

```
Authorization: Bearer <access_token>
```

---

## Auth Endpoints

### POST /auth/register/guest

Register a guest user using a device identifier.

**Request body:**
```json
{ "device_id": "string" }
```

**Response `201`:**
```json
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "user": { "id": "uuid", "device_id": "...", "phone": null, "phone_verified": false, "is_active": true, "created_at": "..." }
}
```

---

### POST /auth/register/phone

Request an SMS verification code.

**Request body:**
```json
{ "phone": "+71234567890" }
```

**Response `200`:**
```json
{ "message": "Verification code sent", "phone": "+71234567890" }
```

---

### POST /auth/verify/phone

Verify the SMS code and receive a JWT token.

**Request body:**
```json
{ "phone": "+71234567890", "code": "123456" }
```

**Response `200`:** Same as `/auth/register/guest` response.

---

### GET /auth/me

Get the current authenticated user.

**Response `200`:**
```json
{ "id": "uuid", "device_id": null, "phone": "+7...", "phone_verified": true, "is_active": true, "created_at": "..." }
```

---

## Location Endpoints

### PUT /location/

Update the current user's location.

**Request body:**
```json
{ "latitude": 55.751244, "longitude": 37.618423 }
```

**Response `200`:** Updated user object.

---

## Room Endpoints

### GET /room/nearby/users

Count active users within a radius.

**Query params:** `latitude`, `longitude`, `radius_meters` (10–200, default 100)

**Response `200`:**
```json
{ "count": 5, "radius_meters": 100 }
```

---

### GET /room/messages

Get anonymous messages from the current room.

**Query params:** `latitude`, `longitude`, `radius_meters`, `limit` (1–100, default 50)

When fewer than 3 real messages exist the response is supplemented with bot
messages so the room never appears empty.

**Response `200`:**
```json
[
  {
    "id": "uuid",
    "text": "Hello from nearby!",
    "created_at": "2024-01-01T12:00:00",
    "reaction_count": 3,
    "user_has_reacted": false,
    "is_mystery": true,
    "author_revealed": false,
    "author_username": null
  }
]
```

`author_revealed` is `true` when:
- The current user is the author.
- Both users have reacted to each other's messages (mutual reaction).
- The message is older than 24 hours.

When `author_revealed` is `true` and an `author_username` is available it contains the author's phone number or device ID.

---

### POST /room/messages

Post an anonymous message to the room.

**Request body:**
```json
{ "text": "Hello!", "latitude": 55.75, "longitude": 37.62 }
```

**Response `201`:** Message object (same shape as GET /room/messages items).

After the message is saved a `message_new` event is broadcast via WebSocket to
all users within the same radius.

---

### POST /room/reactions

Add a reaction to a message.

**Request body:**
```json
{ "message_id": "uuid", "reaction_type": "like" }
```

Allowed `reaction_type`: `like`, `heart`, `laugh`, `sad`, `angry`

**Response `201`:** Reaction object.

---

### DELETE /room/reactions/{message_id}

Remove a reaction.

**Query params:** `reaction_type` (default `like`)

**Response `204`:** No content.

---

## Chat Endpoints

### GET /chat/

List all private chats for the current user.

**Response `200`:**
```json
{
  "chats": [
    {
      "id": "uuid",
      "created_at": "...",
      "other_user_id": "uuid",
      "last_message": "Hey!",
      "last_message_at": "...",
      "unread_count": 0
    }
  ],
  "total": 1
}
```

---

### POST /chat/open/{other_user_id}

Open a private chat (requires mutual interest — both users liked each other's messages).

**Response `201`:** Chat object.

---

### GET /chat/{chat_id}/messages

Get messages in a private chat.

**Query params:** `limit` (1–100, default 50), `offset` (default 0)

**Response `200`:** Array of chat message objects.

---

### POST /chat/{chat_id}/messages

Send a message in a private chat.

**Request body:**
```json
{ "text": "Hey, how are you?" }
```

**Response `201`:** ChatMessage object.

---

## Error Responses

All errors follow this shape:

```json
{ "detail": "Human-readable error message" }
```

| Status | Meaning                       |
|--------|-------------------------------|
| 400    | Bad request / validation error|
| 401    | Unauthorized (invalid token)  |
| 403    | Forbidden                     |
| 404    | Resource not found            |
| 409    | Conflict (duplicate resource) |
| 422    | Unprocessable entity (Pydantic validation failed) |
| 500    | Internal server error         |

---

## WebSocket Endpoint

Base URL: `ws://localhost:8000/ws`

### GET /ws/room

Real-time bidirectional connection for room events.

**Authentication:** Pass the JWT as a query parameter.

**Connection URL:**
```
ws://localhost:8000/ws/room?token=<jwt>&latitude=55.75&longitude=37.62
```

| Query param  | Required | Description                          |
|--------------|----------|--------------------------------------|
| `token`      | ✅       | JWT access token                     |
| `latitude`   | ❌       | Initial latitude (decimal degrees)   |
| `longitude`  | ❌       | Initial longitude (decimal degrees)  |

**Close codes:**
- `4001` — authentication failed / invalid token

---

### Client → Server messages

```json
{ "type": "location_update", "latitude": 55.75, "longitude": 37.62 }
```
Update the current user's location so geo-filtered broadcasts work correctly.

```json
{ "type": "pong" }
```
Response to a server-initiated `ping`.

---

### Server → Client events

#### `message_new`
A new message was posted within the user's radius.
```json
{
  "type": "message_new",
  "data": {
    "id": "uuid",
    "text": "Hello!",
    "created_at": "2024-01-01T12:00:00",
    "reaction_count": 0,
    "user_has_reacted": false,
    "is_mystery": true,
    "author_revealed": false,
    "author_username": null
  }
}
```

#### `reaction_added`
A reaction was added to a message within the user's radius.
```json
{
  "type": "reaction_added",
  "data": { "message_id": "uuid", "new_count": 5 }
}
```

#### `nearby_count_changed`
The number of connected users in the area changed.
```json
{
  "type": "nearby_count_changed",
  "data": { "count": 3 }
}
```

#### `ping`
Keep-alive ping sent every 30 seconds. Respond with `{"type": "pong"}`.
```json
{ "type": "ping" }
```
