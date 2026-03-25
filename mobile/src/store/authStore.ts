import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import type { User } from '@/types';

interface AuthState {
  token: string | null;
  user: User | null;
  isLoading: boolean;
  /** Persist token and user to secure storage. */
  setAuth: (token: string, user: User) => Promise<void>;
  /** Clear auth state and remove from storage. */
  logout: () => Promise<void>;
  /** Load auth state from secure storage (called on app start). */
  loadFromStorage: () => Promise<void>;
}

/**
 * Global authentication store using Zustand.
 * Token is persisted in Expo SecureStore for security.
 */
export const useAuthStore = create<AuthState>((set) => ({
  token: null,
  user: null,
  isLoading: true,

  setAuth: async (token, user) => {
    await SecureStore.setItemAsync('auth_token', token);
    await SecureStore.setItemAsync('auth_user', JSON.stringify(user));
    set({ token, user });
  },

  logout: async () => {
    await SecureStore.deleteItemAsync('auth_token');
    await SecureStore.deleteItemAsync('auth_user');
    set({ token: null, user: null });
  },

  loadFromStorage: async () => {
    try {
      const token = await SecureStore.getItemAsync('auth_token');
      const userJson = await SecureStore.getItemAsync('auth_user');
      const user = userJson ? (JSON.parse(userJson) as User) : null;
      set({ token, user, isLoading: false });
    } catch {
      set({ token: null, user: null, isLoading: false });
    }
  },
}));
