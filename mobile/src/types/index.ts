/**
 * Shared TypeScript types for the Room mobile application.
 * Mirrors the API response schemas from the FastAPI backend.
 */

// ─── User ────────────────────────────────────────────────────────────────────

export interface User {
  id: string;
  device_id: string | null;
  phone: string | null;
  phone_verified: boolean;
  is_active: boolean;
  created_at: string;
}

// ─── Messages ────────────────────────────────────────────────────────────────

export interface Message {
  id: string;
  text: string;
  created_at: string;
  reaction_count: number;
  user_has_reacted: boolean;
  /** Mystery mode — author is hidden until revealed. */
  is_mystery: boolean;
  /** Whether the author has been revealed to the current user. */
  author_revealed: boolean;
  /** Author identifier (only set when author_revealed is true). */
  author_username?: string;
}

// ─── Reactions ───────────────────────────────────────────────────────────────

export interface Reaction {
  id: string;
  message_id: string;
  user_id: string;
  reaction_type: string;
  created_at: string;
}

// ─── Chat ─────────────────────────────────────────────────────────────────────

export interface Chat {
  id: string;
  created_at: string;
  other_user_id: string;
  last_message: string | null;
  last_message_at: string | null;
  unread_count: number;
}

export interface ChatMessage {
  id: string;
  chat_id: string;
  sender_id: string;
  text: string;
  created_at: string;
  is_mine: boolean;
}

// ─── Navigation ──────────────────────────────────────────────────────────────

export type RootStackParamList = {
  Splash: undefined;
  Auth: undefined;
  Permissions: undefined;
  Main: undefined;
  Chat: { chatId: string };
};
