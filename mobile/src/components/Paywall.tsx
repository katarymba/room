/**
 * Paywall component — shown when a free user hits their daily message limit.
 *
 * Displays the premium benefits and subscription options (monthly / yearly).
 * Calls the backend ``POST /api/subscribe`` endpoint to initiate a Stripe
 * Checkout session, then opens the URL in the device browser.
 */
import React, { useState } from 'react';
import {
  ActivityIndicator,
  Linking,
  Modal,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';

import { API_BASE_URL } from '@/utils/constants';
import * as SecureStore from 'expo-secure-store';

// ── Types ─────────────────────────────────────────────────────────────────────

interface PaywallProps {
  visible: boolean;
  onDismiss: () => void;
}

// ── Constants ─────────────────────────────────────────────────────────────────

const PREMIUM_BENEFITS = [
  '✅ Unlimited messages per day',
  '✅ Priority support',
  '✅ Custom reactions',
  '✅ Extended mystery mode duration',
  '✅ Ad-free experience',
];

// ── Component ─────────────────────────────────────────────────────────────────

export default function Paywall({ visible, onDismiss }: PaywallProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubscribe = async (plan: 'monthly' | 'yearly') => {
    setLoading(true);
    setError(null);
    try {
      const token = await SecureStore.getItemAsync('auth_token');
      if (!token) {
        setError('Please log in to subscribe.');
        return;
      }

      const response = await fetch(`${API_BASE_URL}/subscribe?plan=${plan}`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        setError(data?.detail ?? 'Failed to start subscription. Please try again.');
        return;
      }

      const { checkout_url } = await response.json();
      if (checkout_url) {
        await Linking.openURL(checkout_url);
        onDismiss();
      }
    } catch (err) {
      setError('Network error. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal
      visible={visible}
      transparent
      animationType="slide"
      onRequestClose={onDismiss}
    >
      <View style={styles.overlay}>
        <View style={styles.container}>
          {/* Header */}
          <Text style={styles.title}>🚀 Upgrade to Premium</Text>
          <Text style={styles.subtitle}>
            You've reached your daily free message limit.
          </Text>

          {/* Benefits */}
          <View style={styles.benefitsContainer}>
            {PREMIUM_BENEFITS.map((benefit) => (
              <Text key={benefit} style={styles.benefit}>
                {benefit}
              </Text>
            ))}
          </View>

          {/* Error */}
          {error && <Text style={styles.errorText}>{error}</Text>}

          {/* Subscription buttons */}
          {loading ? (
            <ActivityIndicator size="large" color="#6C63FF" style={styles.loader} />
          ) : (
            <View style={styles.buttonsContainer}>
              <TouchableOpacity
                style={[styles.button, styles.primaryButton]}
                onPress={() => handleSubscribe('yearly')}
              >
                <Text style={styles.primaryButtonText}>Yearly — Best Value 🎉</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.button, styles.secondaryButton]}
                onPress={() => handleSubscribe('monthly')}
              >
                <Text style={styles.secondaryButtonText}>Monthly</Text>
              </TouchableOpacity>
            </View>
          )}

          {/* Dismiss */}
          <TouchableOpacity style={styles.dismissButton} onPress={onDismiss}>
            <Text style={styles.dismissText}>Maybe later</Text>
          </TouchableOpacity>
        </View>
      </View>
    </Modal>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.6)',
    justifyContent: 'flex-end',
  },
  container: {
    backgroundColor: '#fff',
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    padding: 28,
    paddingBottom: 40,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1a1a2e',
    textAlign: 'center',
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 15,
    color: '#666',
    textAlign: 'center',
    marginBottom: 20,
  },
  benefitsContainer: {
    marginBottom: 24,
    gap: 8,
  },
  benefit: {
    fontSize: 15,
    color: '#333',
    lineHeight: 22,
  },
  errorText: {
    color: '#e53e3e',
    fontSize: 14,
    textAlign: 'center',
    marginBottom: 12,
  },
  loader: {
    marginVertical: 16,
  },
  buttonsContainer: {
    gap: 12,
    marginBottom: 16,
  },
  button: {
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
  },
  primaryButton: {
    backgroundColor: '#6C63FF',
  },
  primaryButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
  secondaryButton: {
    backgroundColor: '#f0f0f0',
  },
  secondaryButtonText: {
    color: '#333',
    fontSize: 16,
    fontWeight: '500',
  },
  dismissButton: {
    alignItems: 'center',
    paddingVertical: 8,
  },
  dismissText: {
    color: '#999',
    fontSize: 14,
  },
});
