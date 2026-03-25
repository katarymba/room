import { useCallback, useEffect, useRef, useState } from 'react';
import { apiClient } from '@/services/api';
import { wsService } from '@/services/websocket';
import { useLocation } from './useLocation';
import { useMessagesStore } from '@/store/messagesStore';
import { DEFAULT_RADIUS, ROOM_REFRESH_INTERVAL_MS } from '@/utils/constants';
import type { Message } from '@/types';

// Fallback polling interval — increased because WebSocket handles real-time updates
const FALLBACK_POLL_INTERVAL_MS = 60_000;

/**
 * Hook that loads nearby room messages and provides a send function.
 *
 * On mount the hook connects to the WebSocket for real-time updates and falls
 * back to polling (every 60 s) when the connection is unavailable.
 */
export function useMessages() {
  const { location } = useLocation();
  const setMessages = useMessagesStore((state) => state.setMessages);
  const addMessage = useMessagesStore((state) => state.addMessage);
  const updateMessage = useMessagesStore((state) => state.updateMessage);
  const setNearbyCount = useMessagesStore((state) => state.setNearbyCount);
  const messages = useMessagesStore((state) => state.messages);
  const [loading, setLoading] = useState(false);
  const pollTimerRef = useRef<number | null>(null);

  const fetchMessages = useCallback(async () => {
    if (!location) return;
    setLoading(true);
    try {
      const { data: msgs } = await apiClient.get<Message[]>('/room/messages', {
        params: {
          latitude: location.latitude,
          longitude: location.longitude,
          radius_meters: DEFAULT_RADIUS,
        },
      });
      setMessages(msgs);

      const { data: nearbyData } = await apiClient.get<{ count: number }>('/room/nearby/users', {
        params: {
          latitude: location.latitude,
          longitude: location.longitude,
          radius_meters: DEFAULT_RADIUS,
        },
      });
      setNearbyCount(nearbyData.count);
    } catch {
      // Silently fail — show cached messages if any
    } finally {
      setLoading(false);
    }
  }, [location, setMessages, setNearbyCount]);

  // Initial fetch + location-change refetch
  useEffect(() => {
    fetchMessages();
  }, [fetchMessages]);

  // WebSocket real-time updates
  useEffect(() => {
    if (!location) return;

    // Connect (or update location on existing connection)
    wsService.connect(location.latitude, location.longitude);

    const unsubNew = wsService.on<Message>('message_new', (event) => {
      if (event.data) addMessage(event.data);
    });

    const unsubReaction = wsService.on<{ message_id: string; new_count: number }>(
      'reaction_added',
      (event) => {
        if (!event.data) return;
        const { message_id, new_count } = event.data;
        const existing = useMessagesStore.getState().messages.find((m: Message) => m.id === message_id);
        if (existing) {
          updateMessage({ ...existing, reaction_count: new_count });
        }
      },
    );

    const unsubCount = wsService.on<{ count: number }>('nearby_count_changed', (event) => {
      if (event.data !== undefined) setNearbyCount(event.data.count);
    });

    // Fallback polling in case WebSocket is unavailable
    pollTimerRef.current = setInterval(fetchMessages, FALLBACK_POLL_INTERVAL_MS) as unknown as number;

    return () => {
      unsubNew();
      unsubReaction();
      unsubCount();
      if (pollTimerRef.current) {
        clearInterval(pollTimerRef.current);
        pollTimerRef.current = null;
      }
      wsService.disconnect();
    };
  }, [location, addMessage, updateMessage, setNearbyCount, fetchMessages]);

  /** Post a new message to the current room. */
  const sendMessage = useCallback(
    async (text: string) => {
      if (!location) return;
      const { data } = await apiClient.post<Message>('/room/messages', {
        text,
        latitude: location.latitude,
        longitude: location.longitude,
      });
      useMessagesStore.getState().addMessage(data);
    },
    [location],
  );

  return { messages, loading, sendMessage, refresh: fetchMessages };
}
