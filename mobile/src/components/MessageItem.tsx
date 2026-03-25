import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { apiClient } from '@/services/api';
import { useMessagesStore } from '@/store/messagesStore';
import { COLORS, TYPOGRAPHY } from '@/utils/theme';
import type { Message } from '@/types';

interface MessageItemProps {
  message: Message;
}

/**
 * A single message bubble shown in the Room.
 * Displays the message text, creation time, reaction count, and a like button.
 * When mystery mode is active the author is hidden until revealed.
 */
export function MessageItem({ message }: MessageItemProps) {
  const updateMessage = useMessagesStore((state) => state.updateMessage);

  const handleReaction = async () => {
    try {
      if (message.user_has_reacted) {
        await apiClient.delete(`/room/reactions/${message.id}?reaction_type=like`);
        updateMessage({ ...message, reaction_count: message.reaction_count - 1, user_has_reacted: false });
      } else {
        await apiClient.post('/room/reactions', {
          message_id: message.id,
          reaction_type: 'like',
        });
        updateMessage({ ...message, reaction_count: message.reaction_count + 1, user_has_reacted: true });
      }
    } catch {
      // Ignore errors — optimistic update not reverted for simplicity
    }
  };

  const timeLabel = new Date(message.created_at).toLocaleTimeString([], {
    hour: '2-digit',
    minute: '2-digit',
  });

  const authorLabel =
    message.is_mystery && !message.author_revealed
      ? '🎭 Mystery'
      : message.author_revealed && message.author_username
        ? `✨ ${message.author_username}`
        : null;

  return (
    <View style={styles.container}>
      {authorLabel !== null && (
        <Text style={[styles.author, message.author_revealed && styles.authorRevealed]}>
          {authorLabel}
        </Text>
      )}
      <Text style={styles.text}>{message.text}</Text>
      <View style={styles.footer}>
        <Text style={styles.time}>{timeLabel}</Text>
        <TouchableOpacity onPress={handleReaction} style={styles.reactionBtn}>
          <Text style={[styles.reactionIcon, message.user_has_reacted && styles.reactionActive]}>
            ❤️
          </Text>
          {message.reaction_count > 0 && (
            <Text style={styles.reactionCount}>{message.reaction_count}</Text>
          )}
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 12,
    marginVertical: 4,
    borderColor: COLORS.border,
    borderWidth: 1,
  },
  author: {
    ...TYPOGRAPHY.small,
    color: COLORS.textMuted,
    marginBottom: 4,
  },
  authorRevealed: {
    color: COLORS.primary,
  },
  text: {
    ...TYPOGRAPHY.body,
    color: COLORS.text,
    lineHeight: 22,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 8,
  },
  time: {
    ...TYPOGRAPHY.small,
    color: COLORS.textMuted,
  },
  reactionBtn: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  reactionIcon: {
    fontSize: 16,
    opacity: 0.4,
  },
  reactionActive: {
    opacity: 1,
  },
  reactionCount: {
    ...TYPOGRAPHY.small,
    color: COLORS.textMuted,
  },
});
