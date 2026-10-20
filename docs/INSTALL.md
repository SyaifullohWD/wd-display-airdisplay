# Install WD Display

Three ways to install, fastest first. The file you want is **`release/WD-Display-0.1.4-dev.apk`** (28 MB, arm64, Android 10+).

Before you start, confirm the download:

```bash
shasum -a 256 -c SHA256SUMS
# WD-Display-0.1.4-dev.apk: OK
# WD-Display-0.1.4-dev-source.tar.gz: OK
```

Expected APK checksum:

```text
cd671f0386087c7947807c6edcd14dc5b248e8c379fc5601e0a95d3840f9ab4c
```

## 1. Install on the phone directly

1. Copy `WD-Display-0.1.4-dev.apk` to the phone (USB, Google Drive, or download it from the GitHub release page).
2. Open the file with the phone's file manager.
3. Android will refuse the first time and offer a settings shortcut. Allow **Install unknown apps** for whichever app you opened it from (Files, Chrome, Drive).
4. Tap **Install**. Play Protect may warn that the app is not from the Play Store. That is expected: the APK is debug-signed. Choose **Install anyway**.
5. Tap **Open**.

## 2. Install with adb (no permission prompts)

```bash
adb devices                      # confirm your phone is listed and authorized
adb install -r WD-Display-0.1.4-dev.apk
adb shell am start -n org.pocketairdisplay.receiver/.MainActivity
```

If you get `INSTALL_FAILED_UPDATE_INCOMPATIBLE` because an older build with a different signature is installed:

```bash
adb uninstall org.pocketairdisplay.receiver
adb install WD-Display-0.1.4-dev.apk
```

Uninstalling removes saved settings and the connection history for this app only.

## 3. Build it yourself

See the build section of the main [README](../README.md#build-from-source). You need the Android SDK, NDK r27d and a JDK. The build produces `app/build/outputs/apk/debug/app-debug.apk`.

## First run

1. **Notification permission.** Android 13+ shows a prompt. Allowing it gives you a normal notification you can tap to return to the receiver. Denying it does not stop the receiver from starting, but background recovery is more limited.
2. **Overlay access (optional).** Only needed if you want the app to bring itself to the front automatically when a Mac starts streaming. Without it, you tap the notification instead. The app never asks for this on its own.
3. The status card should read **Ready to Connect** and the receiver name is shown under it.

No account, no sign-in, no network setup, nothing to configure on the Mac.

## Updating

Install the new APK over the old one (`adb install -r`, or just open the new file). Settings and history are kept as long as the package stays the same.

## Uninstalling

```bash
adb uninstall org.pocketairdisplay.receiver
```

or long-press the icon and remove it like any other app.

## What gets installed

| Property | Value |
|---|---|
| Package | `org.pocketairdisplay.receiver` |
| Version | `0.1.4-dev` (versionCode 5) |
| Size | 28 MB |
| ABI | `arm64-v8a` only |
| Min Android | 10 (API 29) |
| Target Android | 14 (API 34) |
| Signature | Android debug certificate |
| Permissions | Network, Wi-Fi state, multicast, wake lock, foreground service (connected device), notifications, boot, optional overlay |
| Native libraries | `libpocketairdisplay.so` (receiver), `libandroidx.graphics.path.so` |

The app has no internet-backend permissions beyond your local network, sends no analytics and stores nothing off-device.

## If the install is blocked

- **"App not installed"**: another copy with a different signature is present. Uninstall first.
- **"Unsafe app blocked" / Play Protect**: expected for debug-signed builds. Use the "install anyway" path.
- **"There was a problem parsing the package"**: the download is truncated. Re-download and re-check the SHA-256.
- **"Your device is not compatible"**: the phone is 32-bit. This build is arm64 only.
- **ADB shows the device as `unauthorized`**: unlock the phone and accept the USB debugging prompt.
