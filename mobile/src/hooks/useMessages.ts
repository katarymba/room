import { useCallback, useEffect, useState } from 'react';
import { apiClient } from '@/services/api';
import { useLocation } from './useLocation';
import { useMessagesStore } from '@/store/messagesStore';
import { DEFAULT_RADIUS } from '@/utils/constants';
import type { Message } from '@/types';

/**
 * Hook that loads nearby room messages and provides a send function.
 *
 * Automatically refetches messages when the location changes.
 */
export function useMessages() {
  const { location } = useLocation();
  const setMessages = useMessagesStore((state) => state.setMessages);
  const setNearbyCount = useMessagesStore((state) => state.setNearbyCount);
  const messages = useMessagesStore((state) => state.messages);
  const [loading, setLoading] = useState(false);

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

  // Auto-refresh when location changes
  useEffect(() => {
    fetchMessages();
  }, [fetchMessages]);

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
