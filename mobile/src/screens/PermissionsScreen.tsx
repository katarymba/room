import React, { useState } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  Alert,
  Platform,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import * as Location from 'expo-location';
import { COLORS, TYPOGRAPHY } from '@/utils/theme';
import type { RootStackParamList } from '@/types';

type NavigationProp = NativeStackNavigationProp<RootStackParamList, 'Permissions'>;

/**
 * Permissions screen — requests geolocation (and optionally Bluetooth) from the user.
 * This screen is shown once after initial login.
 */
export function PermissionsScreen() {
  const navigation = useNavigation<NavigationProp>();
  const [locationGranted, setLocationGranted] = useState(false);

  /** Request foreground location permission. */
  const requestLocation = async () => {
    const { status } = await Location.requestForegroundPermissionsAsync();
    if (status === 'granted') {
      setLocationGranted(true);
    } else {
      Alert.alert(
        'Permission Required',
        'Location access is required to find people nearby. Please enable it in Settings.',
      );
    }
  };

  /** Proceed to the main Room screen. */
  const handleContinue = () => {
    if (!locationGranted) {
      Alert.alert('Required', 'Please grant location permission to continue.');
      return;
    }
    navigation.replace('Main' as any);
  };

  return (
    <View style={styles.container}>
      <Text style={styles.title}>Permissions</Text>
      <Text style={styles.subtitle}>
        Room needs access to your location to show people and messages nearby.
      </Text>

      <View style={styles.permissionCard}>
        <Text style={styles.permissionTitle}>📍 Location</Text>
        <Text style={styles.permissionDesc}>
          Used to show nearby messages and count people in your area. Never shared publicly.
        </Text>
        <TouchableOpacity
          style={[styles.btn, locationGranted && styles.btnGranted]}
          onPress={requestLocation}
          disabled={locationGranted}
        >
          <Text style={styles.btnText}>{locationGranted ? '✓ Granted' : 'Grant Access'}</Text>
        </TouchableOpacity>
      </View>

      <TouchableOpacity
        style={[styles.continueBtn, !locationGranted && styles.continueBtnDisabled]}
        onPress={handleContinue}
      >
        <Text style={styles.continueBtnText}>Continue</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
    paddingHorizontal: 24,
    paddingTop: 80,
  },
  title: {
    ...TYPOGRAPHY.h1,
    color: COLORS.text,
    marginBottom: 12,
  },
  subtitle: {
    ...TYPOGRAPHY.body,
    color: COLORS.textMuted,
    marginBottom: 40,
  },
  permissionCard: {
    backgroundColor: COLORS.surface,
    borderRadius: 12,
    padding: 20,
    marginBottom: 16,
    borderColor: COLORS.border,
    borderWidth: 1,
  },
  permissionTitle: {
    ...TYPOGRAPHY.h3,
    color: COLORS.text,
    marginBottom: 8,
  },
  permissionDesc: {
    ...TYPOGRAPHY.small,
    color: COLORS.textMuted,
    marginBottom: 16,
  },
  btn: {
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    paddingVertical: 12,
    alignItems: 'center',
  },
  btnGranted: {
    backgroundColor: COLORS.success,
  },
  btnText: {
    color: COLORS.background,
    fontWeight: '600',
  },
  continueBtn: {
    marginTop: 32,
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    paddingVertical: 16,
    alignItems: 'center',
  },
  continueBtnDisabled: {
    opacity: 0.4,
  },
  continueBtnText: {
    color: COLORS.background,
    fontSize: 16,
    fontWeight: '700',
  },
});
