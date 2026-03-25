import { StyleSheet } from 'react-native';

/**
 * Dark theme colour palette.
 * All colours are defined here to keep the theme consistent and easy to change.
 */
export const COLORS = {
  // Backgrounds
  background: '#0D0D0D',
  surface: '#1A1A1A',
  surfaceElevated: '#252525',

  // Text
  text: '#F0F0F0',
  textMuted: '#888888',
  textDisabled: '#444444',

  // Brand
  primary: '#FFFFFF',
  primaryDark: '#CCCCCC',

  // Semantic
  success: '#4CAF50',
  warning: '#FF9800',
  error: '#F44336',
  info: '#2196F3',

  // UI
  border: '#2A2A2A',
  divider: '#222222',
} as const;

export type ColorKey = keyof typeof COLORS;

/**
 * Typography styles matching the minimal dark theme.
 */
export const TYPOGRAPHY = StyleSheet.create({
  h1: {
    fontSize: 32,
    fontWeight: '700' as const,
    letterSpacing: 0.5,
  },
  h2: {
    fontSize: 22,
    fontWeight: '600' as const,
    letterSpacing: 0.3,
  },
  h3: {
    fontSize: 18,
    fontWeight: '600' as const,
  },
  body: {
    fontSize: 15,
    fontWeight: '400' as const,
    lineHeight: 22,
  },
  small: {
    fontSize: 12,
    fontWeight: '400' as const,
  },
  caption: {
    fontSize: 11,
    fontWeight: '400' as const,
    letterSpacing: 0.3,
  },
});
