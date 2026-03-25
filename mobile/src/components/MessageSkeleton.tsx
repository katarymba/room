import React, { useEffect, useRef } from 'react';
import { Animated, View, StyleSheet } from 'react-native';
import { COLORS } from '@/utils/theme';

/**
 * Pulsing skeleton placeholder shown while messages are loading for the first time.
 */
function SkeletonCard({ delay = 0, width = '100%' }: { delay?: number; width?: string | number }) {
  const opacity = useRef(new Animated.Value(0.3)).current;

  useEffect(() => {
    const pulse = Animated.loop(
      Animated.sequence([
        Animated.timing(opacity, {
          toValue: 1,
          duration: 600,
          delay,
          useNativeDriver: true,
        }),
        Animated.timing(opacity, {
          toValue: 0.3,
          duration: 600,
          useNativeDriver: true,
        }),
      ]),
    );
    pulse.start();
    return () => pulse.stop();
  }, [opacity, delay]);

  return (
    <Animated.View style={[styles.card, { opacity }]}>
      <View style={[styles.line, { width: '75%' }]} />
      <View style={[styles.line, styles.lineShort, { width }]} />
      <View style={styles.footer}>
        <View style={[styles.pill, { width: 40 }]} />
        <View style={[styles.pill, { width: 32 }]} />
      </View>
    </Animated.View>
  );
}

/**
 * A stack of 3 skeleton cards rendered while messages are being fetched.
 */
export function MessageSkeleton() {
  return (
    <View style={styles.container}>
      <SkeletonCard delay={0} width="60%" />
      <SkeletonCard delay={150} width="80%" />
      <SkeletonCard delay={300} width="50%" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    paddingHorizontal: 16,
    paddingTop: 8,
    gap: 8,
  },
  card: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 12,
    borderColor: COLORS.border,
    borderWidth: 1,
    gap: 8,
  },
  line: {
    height: 14,
    borderRadius: 7,
    backgroundColor: COLORS.border,
  },
  lineShort: {
    marginTop: 4,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 4,
  },
  pill: {
    height: 12,
    borderRadius: 6,
    backgroundColor: COLORS.border,
  },
});
