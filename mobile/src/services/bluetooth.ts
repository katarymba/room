/**
 * Bluetooth service — placeholder for offline BLE mode.
 *
 * In a full implementation this module would use expo-bluetooth or
 * react-native-ble-plx to:
 * - Advertise the device presence via BLE
 * - Discover nearby devices
 * - Exchange short messages over BLE GATT characteristics
 *
 * For the MVP this is a no-op stub that logs when called.
 */

export interface BluetoothMessage {
  id: string;
  text: string;
  timestamp: number;
}

let _scanning = false;

/**
 * Start advertising this device via BLE.
 * (Placeholder — not implemented in MVP)
 */
export function startAdvertising(): void {
  console.log('[Bluetooth] startAdvertising — not yet implemented');
}

/**
 * Stop BLE advertising.
 */
export function stopAdvertising(): void {
  console.log('[Bluetooth] stopAdvertising — not yet implemented');
}

/**
 * Start scanning for nearby BLE devices.
 * @param onMessage - Called when a message is received from a nearby device.
 */
export function startScanning(onMessage: (msg: BluetoothMessage) => void): void {
  if (_scanning) return;
  _scanning = true;
  console.log('[Bluetooth] startScanning — not yet implemented');
  // TODO: implement BLE scan and message receive
}

/**
 * Stop BLE scanning.
 */
export function stopScanning(): void {
  _scanning = false;
  console.log('[Bluetooth] stopScanning — not yet implemented');
}

/**
 * Send a short text message to all nearby BLE devices.
 */
export function sendBluetoothMessage(text: string): void {
  console.log('[Bluetooth] sendBluetoothMessage — not yet implemented', text);
  // TODO: broadcast message via BLE GATT
}

/** Whether BLE scanning is currently active. */
export function isScanning(): boolean {
  return _scanning;
}
