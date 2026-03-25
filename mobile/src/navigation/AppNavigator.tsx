import React from 'react';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';

import { SplashScreen } from '@/screens/SplashScreen';
import { AuthScreen } from '@/screens/AuthScreen';
import { PermissionsScreen } from '@/screens/PermissionsScreen';
import { RoomScreen } from '@/screens/RoomScreen';
import { ChatScreen } from '@/screens/ChatScreen';
import { useAuthStore } from '@/store/authStore';
import { COLORS } from '@/utils/theme';
import type { RootStackParamList } from '@/types';

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator();

/** Bottom tab navigator shown to authenticated users. */
function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: COLORS.background,
          borderTopColor: COLORS.border,
        },
        tabBarActiveTintColor: COLORS.primary,
        tabBarInactiveTintColor: COLORS.textMuted,
      }}
    >
      <Tab.Screen
        name="Room"
        component={RoomScreen}
        options={{ title: 'Room' }}
      />
      <Tab.Screen
        name="Chats"
        component={ChatScreen}
        options={{ title: 'Chats' }}
      />
    </Tab.Navigator>
  );
}

/**
 * Root navigation component.
 * Routes unauthenticated users to Auth flow and authenticated users to main app.
 */
export function AppNavigator() {
  const token = useAuthStore((state) => state.token);

  return (
    <NavigationContainer
      theme={{
        dark: true,
        colors: {
          primary: COLORS.primary,
          background: COLORS.background,
          card: COLORS.surface,
          text: COLORS.text,
          border: COLORS.border,
          notification: COLORS.primary,
        },
      }}
    >
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        {!token ? (
          // Auth flow
          <>
            <Stack.Screen name="Splash" component={SplashScreen} />
            <Stack.Screen name="Auth" component={AuthScreen} />
            <Stack.Screen name="Permissions" component={PermissionsScreen} />
          </>
        ) : (
          // Main app
          <Stack.Screen name="Main" component={MainTabs} />
        )}
      </Stack.Navigator>
    </NavigationContainer>
  );
}
