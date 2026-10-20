# Troubleshooting

Work down this list in order. Most problems are network discovery, not the app.

## The phone does not appear in Screen Mirroring

1. **Same network.** Both devices must be on the same subnet. Phone on cellular, or Mac on a VPN, will never see the receiver.
2. **Client isolation.** Guest Wi-Fi networks often block device-to-device traffic. Use the main network.
3. **VPN.** Turn off any VPN on the Mac or the phone. VPNs commonly swallow multicast traffic.
4. **Battery optimization.** Android Settings → Apps → WD Display → Battery → **Unrestricted**. Aggressive power management stops the receiver from advertising when idle.
5. **Name cache.** If you renamed the receiver, the Mac can keep showing the old name. Toggle Wi-Fi off and on, or restart Control Center.
6. **Restart the receiver.** In the app, use the restart action, or force stop and reopen. The status card should read **Ready to Connect**, not an error.
7. **Firewall on the Mac.** A third-party firewall can block inbound discovery traffic. Allow local network access for Control Center.

## It connects but the screen stays black

- **H.265 mismatch.** If you enabled the experimental H.265 setting, turn it off and reconnect. Some phones advertise HEVC decoding but fail on the actual stream profile.
- **Codec failure.** Open the telemetry overlay. If it shows frames arriving with zero decode, the phone's decoder is rejecting the stream. Try a lower resolution on the Mac (System Settings → Displays → choose a smaller scaled resolution).
- **Surface not attached.** If you opened the app and immediately switched away, the video surface may not exist. Return to the app, keep it in the foreground, and reconnect from the Mac.

## Stutter, tearing, or dropped frames

- Move both devices to 5 GHz.
- Move the phone closer to the access point. Video is 10 to 40 Mbps depending on resolution and motion.
- Watch the telemetry overlay: rising bitrate with falling FPS means the network, stable bitrate with falling FPS means the decoder.
- Close other apps that hold a hardware decoder (camera, video players).

## The connection drops after a few minutes

- Check battery optimization again. This is the single most common cause.
- Turn **Run in Background** on, so leaving the app does not stop the receiver.
- Keep the phone plugged in. Below roughly 15% battery, Android throttles background work.
- If the phone's screen locks and the phone sleeps, the receiver may be suspended. Disable aggressive sleep for this app, or keep the screen on.

## The app closes immediately after opening

Fixed in 0.1.1 and later. If you are on an older build, update. Verify what you installed:

```bash
adb shell dumpsys package org.wddisplay.receiver | grep versionName
```

## Install problems

- **"App not installed"**: a build with a different signature is installed. `adb uninstall org.wddisplay.receiver` then install again.
- **Play Protect warning**: expected, the APK is debug-signed. Continue with "install anyway".
- **"Parsing the package"**: truncated download. Re-download and check `shasum -a 256`.
- **"Not compatible"**: the phone is 32-bit. This is an arm64-only build.

## Screen Mirroring lists the phone but the Mac refuses to connect

- Make sure only one sender is connected at a time. The receiver handles a single client.
- Disconnect on the Mac, wait a few seconds, reconnect. AirPlay sessions can get stuck on the sender side.
- Restart the receiver in the app if it has been running for a long time.

## No sound

Audio is intentionally limited in this build. The legacy RAOP audio path is excluded, and `ANNOUNCE` requests are rejected by design. This is a screen receiver. Use the Mac's own speakers or a separate audio route.

## Extended display does not behave like a second desktop

Extended mode is negotiated by macOS, not the app, and it is the least validated part of this project. If the Mac only offers mirroring, or the extended space is unusable:

- Update macOS, then reconnect.
- Try a different scaled resolution for the WD Display screen in System Settings → Displays.
- Report it with your macOS version, phone model, and what you saw. That is genuinely useful information, because this path is under-tested.

## Something is wrong and the log would help

```bash
adb logcat -d | grep -i -E "pocketairdisplay|WD Display|raop|airplay"
```

Include the app version (`adb shell dumpsys package org.wddisplay.receiver | grep versionName`), your phone model, Android version, macOS version, and whether the connection was direct Wi-Fi or a hotspot.

## Reset the receiver

Clearing app storage resets the service name, settings and history:

```bash
adb shell pm clear org.wddisplay.receiver
```

The receiver restarts with defaults on next launch.
