import React, { useEffect } from 'react';
import { View, Text, StyleSheet, ActivityIndicator } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { useAuthStore } from '@/store/authStore';
import { COLORS, TYPOGRAPHY } from '@/utils/theme';
import type { RootStackParamList } from '@/types';

type NavigationProp = NativeStackNavigationProp<RootStackParamList, 'Splash'>;

/**
 * Splash screen shown while the app initialises.
 * Redirects to Auth if not logged in, or to Main if authenticated.
 */
export function SplashScreen() {
  const navigation = useNavigation<NavigationProp>();
  const token = useAuthStore((state) => state.token);
  const isLoading = useAuthStore((state) => state.isLoading);

  useEffect(() => {
    if (!isLoading) {
      if (token) {
        navigation.replace('Main' as any);
      } else {
        navigation.replace('Auth');
      }
    }
  }, [isLoading, token, navigation]);

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Room</Text>
      <Text style={styles.subtitle}>Anonymous chat nearby</Text>
      <ActivityIndicator color={COLORS.primary} style={styles.loader} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    ...TYPOGRAPHY.h1,
    color: COLORS.text,
    letterSpacing: 8,
    marginBottom: 8,
  },
  subtitle: {
    ...TYPOGRAPHY.body,
    color: COLORS.textMuted,
    marginBottom: 40,
  },
  loader: {
    marginTop: 20,
  },
});
