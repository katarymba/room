/**
 * WebSocket service for real-time room communication.
 *
 * Manages a persistent connection to the backend `/ws/room` endpoint,
 * handles automatic reconnect with exponential back-off, and dispatches
 * incoming server events to registered listeners.
 */
import * as SecureStore from 'expo-secure-store';
import { API_BASE_URL, DEFAULT_RADIUS, LOCATION_UPDATE_INTERVAL_MS } from '@/utils/constants';

// ── Types ─────────────────────────────────────────────────────────────────────

export type WsEventType =
  | 'message_new'
  | 'reaction_added'
  | 'nearby_count_changed'
  | 'ping'
  | 'connected'
  | 'disconnected';

export interface WsEvent<T = unknown> {
  type: WsEventType;
  data?: T;
}

type Listener<T = unknown> = (event: WsEvent<T>) => void;

// ── Constants ─────────────────────────────────────────────────────────────────

const WS_BASE_URL = API_BASE_URL.replace(/^http/, 'ws').replace(/\/api$/, '');
const MAX_RECONNECT_DELAY_MS = 30_000;
const INITIAL_RECONNECT_DELAY_MS = 1_000;

// ── WebSocketService ──────────────────────────────────────────────────────────

class WebSocketService {
  private ws: WebSocket | null = null;
  private reconnectDelay = INITIAL_RECONNECT_DELAY_MS;
  private reconnectTimer: number | null = null;
  private locationTimer: number | null = null;
  private listeners: Map<WsEventType, Set<Listener>> = new Map();
  private currentLat: number | null = null;
  private currentLng: number | null = null;
  private shouldReconnect = false;

  // ── Lifecycle ───────────────────────────────────────────────────────────────

  async connect(latitude?: number, longitude?: number): Promise<void> {
    this.shouldReconnect = true;
    if (latitude !== undefined) this.currentLat = latitude;
    if (longitude !== undefined) this.currentLng = longitude;

    const token = await SecureStore.getItemAsync('auth_token');
    if (!token) return;

    const url = `${WS_BASE_URL}/ws/room`;

    try {
      this.ws = new WebSocket(url);
    } catch {
      this._scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      this.reconnectDelay = INITIAL_RECONNECT_DELAY_MS;

      // Send authentication as the very first message so the token is never
      // exposed in the URL or server access logs.
      const authPayload: Record<string, unknown> = { type: 'auth', token };
      if (this.currentLat !== null) authPayload.latitude = this.currentLat;
      if (this.currentLng !== null) authPayload.longitude = this.currentLng;
      this._send(authPayload);

      this._emit({ type: 'connected' });
      this._startLocationUpdates();
    };

    this.ws.onmessage = (event) => {
      try {
        const parsed: WsEvent = JSON.parse(event.data as string);
        if (parsed.type === 'ping') {
          this._send({ type: 'pong' });
          return;
        }
        this._emit(parsed);
      } catch {
        // ignore malformed frames
      }
    };

    this.ws.onerror = () => {
      // onclose will fire immediately after
    };

    this.ws.onclose = () => {
      this._stopLocationUpdates();
      this._emit({ type: 'disconnected' });
      if (this.shouldReconnect) {
        this._scheduleReconnect();
      }
    };
  }

  disconnect(): void {
    this.shouldReconnect = false;
    this._clearReconnectTimer();
    this._stopLocationUpdates();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  // ── Location ────────────────────────────────────────────────────────────────

  updateLocation(latitude: number, longitude: number): void {
    this.currentLat = latitude;
    this.currentLng = longitude;
    this._send({ type: 'location_update', latitude, longitude });
  }

  // ── Event listeners ─────────────────────────────────────────────────────────

  on<T = unknown>(type: WsEventType, listener: Listener<T>): () => void {
    if (!this.listeners.has(type)) {
      this.listeners.set(type, new Set());
    }
    this.listeners.get(type)!.add(listener as Listener);
    return () => this.off(type, listener);
  }

  off<T = unknown>(type: WsEventType, listener: Listener<T>): void {
    this.listeners.get(type)?.delete(listener as Listener);
  }

  // ── Private helpers ──────────────────────────────────────────────────────────

  private _emit(event: WsEvent): void {
    this.listeners.get(event.type)?.forEach((fn) => {
      try {
        fn(event);
      } catch {
        // ignore listener errors
      }
    });
  }

  private _send(payload: Record<string, unknown>): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(payload));
    }
  }

  private _scheduleReconnect(): void {
    this._clearReconnectTimer();
    this.reconnectTimer = setTimeout(() => {
      this.reconnectDelay = Math.min(this.reconnectDelay * 2, MAX_RECONNECT_DELAY_MS);
      void this.connect();
    }, this.reconnectDelay) as unknown as number;
  }

  private _clearReconnectTimer(): void {
    if (this.reconnectTimer !== null) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
  }

  private _startLocationUpdates(): void {
    this._stopLocationUpdates();
    if (this.currentLat === null || this.currentLng === null) return;
    this.locationTimer = setInterval(() => {
      if (this.currentLat !== null && this.currentLng !== null) {
        this._send({
          type: 'location_update',
          latitude: this.currentLat,
          longitude: this.currentLng,
        });
      }
    }, LOCATION_UPDATE_INTERVAL_MS) as unknown as number;
  }

  private _stopLocationUpdates(): void {
    if (this.locationTimer !== null) {
      clearInterval(this.locationTimer);
      this.locationTimer = null;
    }
  }
}

/** Singleton WebSocket service used throughout the app. */
export const wsService = new WebSocketService();
