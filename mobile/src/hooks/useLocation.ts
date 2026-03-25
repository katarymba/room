import { useEffect, useRef, useState } from 'react';
import type { LocationSubscription } from 'expo-location';
import { getCurrentLocation, watchLocation, updateLocationOnServer } from '@/services/location';
import type { Coordinates } from '@/services/location';

/**
 * Hook that tracks the user's current location and syncs it to the backend.
 *
 * - Gets an initial fix on mount
 * - Starts watching for position updates
 * - Pushes each update to the server
 */
export function useLocation() {
  const [location, setLocation] = useState<Coordinates | null>(null);
  const [error, setError] = useState<string | null>(null);
  const subscriptionRef = useRef<LocationSubscription | null>(null);

  useEffect(() => {
    let mounted = true;

    const init = async () => {
      try {
        // Get immediate position
        const coords = await getCurrentLocation();
        if (mounted) setLocation(coords);
        await updateLocationOnServer(coords);

        // Watch for subsequent changes
        subscriptionRef.current = await watchLocation(async (coords) => {
          if (!mounted) return;
          setLocation(coords);
          try {
            await updateLocationOnServer(coords);
          } catch {
            // Non-fatal: continue tracking locally
          }
        });
      } catch (err: any) {
        if (mounted) setError(err.message ?? 'Location error');
      }
    };

    init();

    return () => {
      mounted = false;
      subscriptionRef.current?.remove();
    };
  }, []);

  return { location, error };
}
