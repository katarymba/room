import React, { useEffect } from 'react';
import { StatusBar } from 'expo-status-bar';
import * as SplashScreen from 'expo-splash-screen';
import { AppNavigator } from '@/navigation/AppNavigator';
import { useAuthStore } from '@/store/authStore';

// Keep splash screen visible while loading
SplashScreen.preventAutoHideAsync();

/**
 * Root application component.
 * Initialises auth state and renders the navigation tree.
 */
export default function App() {
  const loadAuth = useAuthStore((state) => state.loadFromStorage);

  useEffect(() => {
    (async () => {
      await loadAuth();
      await SplashScreen.hideAsync();
    })();
  }, [loadAuth]);

  return (
    <>
      <StatusBar style="light" />
      <AppNavigator />
    </>
  );
}
