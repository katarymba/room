import * as Location from 'expo-location';
import { apiClient } from './api';

export interface Coordinates {
  latitude: number;
  longitude: number;
}

/**
 * Request foreground location permission.
 * Returns true if granted, false otherwise.
 */
export async function requestLocationPermission(): Promise<boolean> {
  const { status } = await Location.requestForegroundPermissionsAsync();
  return status === 'granted';
}

/**
 * Get the current device location once.
 * Throws if permission is not granted or location unavailable.
 */
export async function getCurrentLocation(): Promise<Coordinates> {
  const { status } = await Location.getForegroundPermissionsAsync();
  if (status !== 'granted') {
    throw new Error('Location permission not granted');
  }

  const position = await Location.getCurrentPositionAsync({
    accuracy: Location.Accuracy.Balanced,
  });

  return {
    latitude: position.coords.latitude,
    longitude: position.coords.longitude,
  };
}

/**
 * Start watching the device location and call the callback on each update.
 * Returns a subscription object; call `.remove()` to stop watching.
 */
export async function watchLocation(
  callback: (coords: Coordinates) => void,
  intervalMs: number = 10_000,
): Promise<Location.LocationSubscription> {
  const { status } = await Location.getForegroundPermissionsAsync();
  if (status !== 'granted') {
    throw new Error('Location permission not granted');
  }

  return Location.watchPositionAsync(
    {
      accuracy: Location.Accuracy.Balanced,
      timeInterval: intervalMs,
      distanceInterval: 10,
    },
    (position) => {
      callback({
        latitude: position.coords.latitude,
        longitude: position.coords.longitude,
      });
    },
  );
}

/**
 * Update the user's location on the backend.
 */
export async function updateLocationOnServer(coords: Coordinates): Promise<void> {
  await apiClient.put('/location/', coords);
}
