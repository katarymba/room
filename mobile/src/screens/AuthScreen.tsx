import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  StyleSheet,
  Alert,
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import type { NativeStackNavigationProp } from '@react-navigation/native-stack';
import { apiClient } from '@/services/api';
import { useAuthStore } from '@/store/authStore';
import { COLORS, TYPOGRAPHY } from '@/utils/theme';
import type { RootStackParamList } from '@/types';

type NavigationProp = NativeStackNavigationProp<RootStackParamList, 'Auth'>;

/**
 * Authentication screen.
 * Supports guest login (via device ID) and phone-based login.
 */
export function AuthScreen() {
  const navigation = useNavigation<NavigationProp>();
  const setAuth = useAuthStore((state) => state.setAuth);

  const [mode, setMode] = useState<'guest' | 'phone'>('guest');
  const [phone, setPhone] = useState('');
  const [code, setCode] = useState('');
  const [codeSent, setCodeSent] = useState(false);
  const [loading, setLoading] = useState(false);

  /** Login as a guest using a generated device ID. */
  const handleGuestLogin = async () => {
    setLoading(true);
    try {
      const deviceId = `guest_${Date.now()}_${Math.random().toString(36).slice(2)}`;
      const { data } = await apiClient.post('/auth/register/guest', { device_id: deviceId });
      setAuth(data.access_token, data.user);
      navigation.replace('Permissions');
    } catch (err) {
      Alert.alert('Error', 'Could not log in as guest. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  /** Request SMS verification code. */
  const handleRequestCode = async () => {
    if (!phone.trim()) {
      Alert.alert('Validation', 'Please enter a phone number');
      return;
    }
    setLoading(true);
    try {
      await apiClient.post('/auth/register/phone', { phone: phone.trim() });
      setCodeSent(true);
    } catch (err) {
      Alert.alert('Error', 'Could not send verification code.');
    } finally {
      setLoading(false);
    }
  };

  /** Verify the SMS code. */
  const handleVerifyCode = async () => {
    if (!code.trim()) {
      Alert.alert('Validation', 'Please enter the verification code');
      return;
    }
    setLoading(true);
    try {
      const { data } = await apiClient.post('/auth/verify/phone', {
        phone: phone.trim(),
        code: code.trim(),
      });
      setAuth(data.access_token, data.user);
      navigation.replace('Permissions');
    } catch (err) {
      Alert.alert('Error', 'Invalid verification code.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View style={styles.inner}>
        <Text style={styles.title}>Room</Text>
        <Text style={styles.subtitle}>Anonymous chat with people nearby</Text>

        {/* Mode selector */}
        <View style={styles.modeRow}>
          <TouchableOpacity
            style={[styles.modeBtn, mode === 'guest' && styles.modeBtnActive]}
            onPress={() => setMode('guest')}
          >
            <Text style={[styles.modeBtnText, mode === 'guest' && styles.modeBtnTextActive]}>
              Guest
            </Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[styles.modeBtn, mode === 'phone' && styles.modeBtnActive]}
            onPress={() => setMode('phone')}
          >
            <Text style={[styles.modeBtnText, mode === 'phone' && styles.modeBtnTextActive]}>
              Phone
            </Text>
          </TouchableOpacity>
        </View>

        {mode === 'guest' ? (
          <TouchableOpacity style={styles.primaryBtn} onPress={handleGuestLogin} disabled={loading}>
            {loading ? (
              <ActivityIndicator color={COLORS.background} />
            ) : (
              <Text style={styles.primaryBtnText}>Enter as Guest</Text>
            )}
          </TouchableOpacity>
        ) : (
          <>
            <TextInput
              style={styles.input}
              placeholder="+7 000 000 00 00"
              placeholderTextColor={COLORS.textMuted}
              value={phone}
              onChangeText={setPhone}
              keyboardType="phone-pad"
              autoComplete="tel"
            />
            {codeSent && (
              <TextInput
                style={styles.input}
                placeholder="6-digit code"
                placeholderTextColor={COLORS.textMuted}
                value={code}
                onChangeText={setCode}
                keyboardType="number-pad"
                maxLength={6}
              />
            )}
            <TouchableOpacity
              style={styles.primaryBtn}
              onPress={codeSent ? handleVerifyCode : handleRequestCode}
              disabled={loading}
            >
              {loading ? (
                <ActivityIndicator color={COLORS.background} />
              ) : (
                <Text style={styles.primaryBtnText}>
                  {codeSent ? 'Verify Code' : 'Send Code'}
                </Text>
              )}
            </TouchableOpacity>
          </>
        )}
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  inner: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
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
    textAlign: 'center',
    marginBottom: 40,
  },
  modeRow: {
    flexDirection: 'row',
    marginBottom: 24,
    borderRadius: 8,
    overflow: 'hidden',
    borderColor: COLORS.border,
    borderWidth: 1,
  },
  modeBtn: {
    flex: 1,
    paddingVertical: 12,
    alignItems: 'center',
    backgroundColor: COLORS.surface,
  },
  modeBtnActive: {
    backgroundColor: COLORS.primary,
  },
  modeBtnText: {
    color: COLORS.textMuted,
    fontWeight: '600',
  },
  modeBtnTextActive: {
    color: COLORS.background,
  },
  input: {
    width: '100%',
    backgroundColor: COLORS.surface,
    borderRadius: 8,
    paddingHorizontal: 16,
    paddingVertical: 14,
    color: COLORS.text,
    fontSize: 16,
    marginBottom: 12,
    borderColor: COLORS.border,
    borderWidth: 1,
  },
  primaryBtn: {
    width: '100%',
    backgroundColor: COLORS.primary,
    borderRadius: 8,
    paddingVertical: 16,
    alignItems: 'center',
    marginTop: 8,
  },
  primaryBtnText: {
    color: COLORS.background,
    fontSize: 16,
    fontWeight: '700',
  },
});
