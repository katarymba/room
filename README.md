# Room — Anonymous Location-Based Chat

Mobile application for anonymous communication with people nearby (online and offline modes).

## Project Overview

Room is a mobile app that enables anonymous conversations with people in close geographic proximity. It supports both online (internet) and offline (Bluetooth/mesh) modes.

### Target Audience
- Age: 16-30 years
- Students and active social media users (especially TikTok)

### Tech Stack

**Mobile:**
- React Native (iOS + Android)

**Backend:**
- FastAPI
- PostgreSQL

## Features (MVP)

### Core Functionality
- Simple authentication (phone/SMS or guest mode)
- Geolocation (50-200m radius)
- "Room" — main screen showing nearby users and anonymous messages
- Anonymous messaging
- Reactions (likes ❤️)
- Private chats (unlocked by mutual likes)
- Offline mode via Bluetooth Low Energy

### Development Phases

**Phase 1 (MVP):**
- Authentication
- Geolocation
- Room
- Messages
- Reactions

**Phase 2:**
- Private chats
- Notifications

**Phase 3:**
- Offline mode (Bluetooth)

## Project Structure

```
room/
├── mobile/          # React Native app
├── backend/         # FastAPI backend
└── docs/           # Documentation
```

## Getting Started

See README files in respective directories:
- [Mobile App](./mobile/README.md)
- [Backend](./backend/README.md)

## License

MIT
