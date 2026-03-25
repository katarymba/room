import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { COLORS, TYPOGRAPHY } from '@/utils/theme';

interface UserCounterProps {
  /** Number of users in the current room. */
  count: number;
}

/**
 * Displays how many people are currently in the room (nearby).
 */
export function UserCounter({ count }: UserCounterProps) {
  return (
    <View style={styles.container}>
      <Text style={styles.dot}>●</Text>
      <Text style={styles.label}>
        {count} {count === 1 ? 'person' : 'people'} nearby
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  dot: {
    color: COLORS.success,
    fontSize: 10,
  },
  label: {
    ...TYPOGRAPHY.small,
    color: COLORS.textMuted,
  },
});
