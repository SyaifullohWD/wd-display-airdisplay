<div align="center">

<img src="release/icon.png" width="128" alt="WD Display icon">

# WD Display

**Turn an Android phone into a wireless second screen for a Mac, using the Mac's own Screen Mirroring menu.**

No companion app on the Mac. No subscription. No session limits.

Free and open source under GPLv3.

</div>

---

## What it is

WD Display is an AirPlay receiver for Android. It advertises itself on your network the way an Apple TV or a HomePod does, so your Mac lists it in **Control Center → Screen Mirroring** without any extra software on the Mac side.

You open the app on the phone, open Screen Mirroring on the Mac, pick "WD Display", and the Mac's display appears on the phone.

This is a practical alternative to paid receivers, which typically charge for extended sessions or time-limit the free tier.

## Features

| | |
|---|---|
| Native Mac discovery | Appears in the macOS Screen Mirroring list over mDNS, with no sender app |
| H.264 video | Hardware decode through Android MediaCodec into a `SurfaceView` |
| H.265 (optional) | Off by default. Enable it in settings on phones whose decoder supports it |
| Extended display | macOS decides mirror vs. extended in System Settings → Displays |
| Screen orientation lock | Landscape, portrait, or automatic from the phone's sensor |
| Custom receiver name | Choose the name your Mac shows in the picker |
| Runs in background | Optional foreground receiver, with a notification you can tap to return |
| Start on boot | Optional, so the receiver is ready when you sit down |
| Connection history | Last 10 sessions with resolution, codec and duration |
| No account, no telemetry | Nothing leaves your network. No analytics, no cloud |

## Requirements

- **Android 10 or newer (API 29+), arm64-v8a.** 32-bit devices are not supported.
- **Both devices on the same local network** (same Wi-Fi, or both on the phone's hotspot).
- **macOS** with Control Center → Screen Mirroring. Recent macOS versions only.

Discovery uses mDNS on the local subnet. It does not cross NAT, and it does not use Apple's peer-to-peer AWDL link, so there is no router-free "tap to connect" mode like AirDrop has.

## Install

### Fastest: sideload the APK

1. Download **[`release/WD-Display-0.2.1-dev.apk`](release/WD-Display-0.2.1-dev.apk)** (28 MB).
2. On the phone, open the file. Android asks you to allow installs from that app the first time (Settings → Apps → Special access → Install unknown apps).
3. Tap Install, then Open.

The APK is debug-signed, so Play Protect may show a warning. That is expected for an unsigned-by-Google build. Choose "Install anyway".

### Or with adb

```bash
adb install -r WD-Display-0.2.1-dev.apk
adb shell am start -n org.wddisplay.receiver/.MainActivity
```

Verify the download first if you want:

```bash
shasum -a 256 -c SHA256SUMS
```

Full steps, including the notification prompt and permission notes, are in **[docs/INSTALL.md](docs/INSTALL.md)**.

## Use

1. Open WD Display on the phone. The status card reads **Ready to Connect**.
2. On the Mac, open **Control Center → Screen Mirroring** and pick **WD Display**.
3. The phone shows the Mac's display.
4. For a second desktop instead of a copy, go to **macOS System Settings → Displays** and choose **Use as Extended Display**. The Mac decides this, not the app.

Details, settings explanations and the extended-desktop caveat: **[docs/USAGE.md](docs/USAGE.md)**.

## Status, honestly

**Verified**

- Clean build from source with all host gates green: 75 JVM tests, native sanitizer suites, production protocol-handler assertions, 16 KiB ELF and ZIP alignment, APK signature verification.
- On a Samsung Galaxy A55 (SM-A556E, Android 16): install, cold launch, foreground service startup and six isolated lifecycle regression classes all pass.
- Mirroring from a Mac to the phone works on the developer's own setup.

**Not verified**

- Extended desktop as a separate, independently usable second screen.
- Phone-hotspot-only operation (works only if the phone forwards multicast).
- Sustained sessions beyond casual use, rotation changes mid-stream, reconnect after sleep.
- Devices with 16 KiB memory pages (the build is alignment-correct, but runtime on such a device is untested).

Do not buy this expecting a guaranteed macOS Sidecar replacement. It is a working receiver with a short, honest list of unknowns.

## Build from source

Toolchain: Android Studio JBR, project-local Android SDK and NDK r27d, Gradle wrapper.

```bash
export JAVA_HOME="/Applications/Android Studio.app/Contents/jbr/Contents/Home"
export ANDROID_HOME="$PWD/.tools/sdk"
export ANDROID_NDK_HOME="$PWD/.tools/ndk-r27d"

./gradlew :app:assembleDebug          # APK only
./scripts/build.sh                    # full host gates + staged publication
```

Architecture, protocol notes and the security decisions behind the native layer: **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)**.

## Repository layout

```text
app/                  Android app: Compose UI, JNI bridge, MediaCodec pipeline
app/src/main/cpp/     Native AirPlay receiver (derived from UxPlay/Wormhole)
docs/                 Install, usage, architecture, troubleshooting
design/               Icon sources and branding notes
release/              Distributable APK, source bundle, checksums
scripts/              Build, test, packaging and publication gates
tests/                Host-side regression and delivery tests
```

## License and source obligation

GPLv3. See [LICENSE](LICENSE) and [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).

Because this project is GPLv3, every distributed binary ships with corresponding source: **[`release/WD-Display-0.2.1-dev-source.tar.gz`](release/WD-Display-0.2.1-dev-source.tar.gz)**. If you rebuild and redistribute the APK, keep that bundle alongside it.

Derived from [Wormhole Display](https://github.com/pgodlews/wormhole-display), which builds on the UxPlay AirPlay core. Legacy RAOP/AirTunes audio is deliberately excluded: no RSA private key ships in this tree, and audio ANNOUNCE requests are rejected. Only ordinary screen interoperability is implemented, with no DRM or protected-content support.

## Changelog

See [CHANGELOG.md](CHANGELOG.md).
