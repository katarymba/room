import { Platform } from 'react-native';

/** Base URL of the backend API. Override via .env. */
export const API_BASE_URL: string =
  process.env.EXPO_PUBLIC_API_URL ?? 'http://localhost:8000/api';

/** Default geolocation search radius in meters. */
export const DEFAULT_RADIUS = 100;

/** Maximum allowed geolocation search radius in meters. */
export const MAX_RADIUS = 200;

/** How often to refresh the room (milliseconds). */
export const ROOM_REFRESH_INTERVAL_MS = 15_000;

/** How often to push location updates to the server (milliseconds). */
export const LOCATION_UPDATE_INTERVAL_MS = 10_000;

/** Maximum message length (characters). */
export const MAX_MESSAGE_LENGTH = 500;

/** Maximum chat message length (characters). */
export const MAX_CHAT_MESSAGE_LENGTH = 1000;

/** App name shown in the UI. */
export const APP_NAME = 'Room';
