import { create } from 'zustand';
import type { Message } from '@/types';

interface MessagesState {
  messages: Message[];
  nearbyCount: number;
  setMessages: (messages: Message[]) => void;
  addMessage: (message: Message) => void;
  updateMessage: (message: Message) => void;
  setNearbyCount: (count: number) => void;
  clear: () => void;
}

/**
 * Global messages store using Zustand.
 * Holds the current room messages and nearby user count.
 */
export const useMessagesStore = create<MessagesState>((set) => ({
  messages: [],
  nearbyCount: 0,

  setMessages: (messages) => set({ messages }),

  addMessage: (message) =>
    set((state) => ({ messages: [message, ...state.messages] })),

  updateMessage: (updated) =>
    set((state) => ({
      messages: state.messages.map((m) => (m.id === updated.id ? updated : m)),
    })),

  setNearbyCount: (nearbyCount) => set({ nearbyCount }),

  clear: () => set({ messages: [], nearbyCount: 0 }),
}));
