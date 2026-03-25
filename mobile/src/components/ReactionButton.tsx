import React from 'react';
import { TouchableOpacity, Text, StyleSheet } from 'react-native';
import { COLORS, TYPOGRAPHY } from '@/utils/theme';

interface ReactionButtonProps {
  /** Emoji or text label for the reaction. */
  emoji: string;
  count: number;
  active: boolean;
  onPress: () => void;
}

/**
 * Reusable reaction button component.
 * Shows an emoji with an optional count, highlighted when the user has reacted.
 */
export function ReactionButton({ emoji, count, active, onPress }: ReactionButtonProps) {
  return (
    <TouchableOpacity
      style={[styles.btn, active && styles.btnActive]}
      onPress={onPress}
      activeOpacity={0.7}
    >
      <Text style={styles.emoji}>{emoji}</Text>
      {count > 0 && <Text style={[styles.count, active && styles.countActive]}>{count}</Text>}
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  btn: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 16,
    borderColor: COLORS.border,
    borderWidth: 1,
    backgroundColor: COLORS.surface,
    gap: 4,
  },
  btnActive: {
    borderColor: COLORS.primary,
    backgroundColor: `${COLORS.primary}22`,
  },
  emoji: {
    fontSize: 16,
  },
  count: {
    ...TYPOGRAPHY.small,
    color: COLORS.textMuted,
  },
  countActive: {
    color: COLORS.primary,
  },
});
