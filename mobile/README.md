# Room — Mobile App

React Native (Expo) application for anonymous location-based chat.

## Stack

- **Expo** ~50
- **React Navigation** v6 (stack + bottom tabs)
- **Zustand** — state management
- **Axios** — API client
- **TypeScript** — strict mode

## Getting Started

### Prerequisites

- Node.js 18+
- npm or yarn
- Expo CLI (`npm install -g expo-cli`)
- iOS Simulator or Android Emulator (or Expo Go on a physical device)

### Installation

```bash
cd mobile
npm install
```

### Running

```bash
# Start development server
npm start

# iOS
npm run ios

# Android
npm run android
```

### Environment Variables

Copy `.env.example` to `.env` and set the values:

```bash
cp .env.example .env
```

| Variable               | Description                  | Default                       |
|------------------------|------------------------------|-------------------------------|
| `EXPO_PUBLIC_API_URL`  | Backend API base URL         | `http://localhost:8000/api`   |

## Project Structure

```
mobile/
├── App.tsx                     # Root component
├── src/
│   ├── screens/                # Screen components
│   │   ├── SplashScreen.tsx
│   │   ├── AuthScreen.tsx      # Guest or phone login
│   │   ├── PermissionsScreen.tsx
│   │   ├── RoomScreen.tsx      # Main anonymous chat room
│   │   └── ChatScreen.tsx      # Private 1-on-1 chats
│   ├── components/             # Reusable UI components
│   │   ├── MessageItem.tsx
│   │   ├── ReactionButton.tsx
│   │   └── UserCounter.tsx
│   ├── services/               # External integrations
│   │   ├── api.ts              # Axios client
│   │   ├── location.ts         # Expo Location wrapper
│   │   └── bluetooth.ts        # BLE stub (Phase 3)
│   ├── hooks/
│   │   ├── useLocation.ts      # Location tracking hook
│   │   └── useMessages.ts      # Room messages hook
│   ├── navigation/
│   │   └── AppNavigator.tsx    # Navigation tree
│   ├── store/
│   │   ├── authStore.ts        # Auth state (Zustand)
│   │   └── messagesStore.ts    # Messages state (Zustand)
│   ├── utils/
│   │   ├── constants.ts        # App-wide constants
│   │   └── theme.ts            # Dark theme palette
│   └── types/
│       └── index.ts            # TypeScript interfaces
```

## Features

- **Guest login** — instant access using device ID
- **Phone login** — SMS verification flow
- **Room** — see anonymous messages from people within 100m
- **Reactions** — like messages to show interest
- **Private chats** — unlocked when both users like each other
- **Dark theme** — minimalist design

## Development Notes

- Location is tracked every 10s and pushed to the backend
- Messages auto-refresh every 15s or on pull-to-refresh
- Auth token stored securely via `expo-secure-store`
- Bluetooth mode (Phase 3) is stubbed in `services/bluetooth.ts`
