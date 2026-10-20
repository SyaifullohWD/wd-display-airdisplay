# Architecture

## Shape of the system

```text
┌──────────────────────────── Mac (sender) ────────────────────────────┐
│ Control Center → Screen Mirroring → picks "WD Display" over mDNS      │
│ RTSP/HTTP control  +  encrypted H.264/HEVC video over TCP             │
└───────────────────────────────────┬──────────────────────────────────┘
                                    │  same LAN / hotspot
┌───────────────────────────────────▼──────────────────────────────────┐
│ Android app (org.wddisplay.receiver)                                 │
│                                                                      │
│  Compose UI ── WormholeServer (state, identity, history)             │
│       │              │                                               │
│       │              └── WormholeService (foreground, wake lock)     │
│       │                                                              │
│       │        NativeBridge (JNI)                                    │
│       │              │                                               │
│       │        libpocketairdisplay.so                                │
│       │         ├── mDNS registration (_raop._tcp, _airplay._tcp)    │
│       │         ├── HTTP/RTSP control (mdnsd, llhttp, raop handlers) │
│       │         ├── AES-CTR stream decryption (mirror_buffer)        │
│       │         └── frame callbacks → JVM                            │
│       │                                                              │
│       └── VideoRenderer: MediaCodec decoder → SurfaceView            │
└──────────────────────────────────────────────────────────────────────┘
```

## Layers

**Install identity.** The application id is `org.wddisplay.receiver`. The code package is `org.pocketairdisplay.receiver`, inherited from the upstream project, so activity and JNI class names stay there. Both appear together in components: `org.wddisplay.receiver/org.pocketairdisplay.receiver.MainActivity`.

**UI (Kotlin, Jetpack Compose).** A single dashboard: title, status card, connection details, orientation control, grouped settings, connection history, and a diagnostics overlay. Design tokens live in `WdTheme.kt`; the UI layer contains no raw color literals. Light and dark appearances both resolve.

**Receiver controller (Kotlin).** `WormholeServer` owns receiver state: identity and persisted settings, the current client name, mirroring state, video aspect ratio, telemetry and the last 10 sessions. `WormholeService` keeps the receiver alive as a foreground service with a wake lock, and handles boot start.

**JNI bridge.** `NativeBridge` starts and stops the native receiver, receives lifecycle and frame callbacks, and passes through the display geometry the native side advertises. Java strings cross as standard UTF-8 with a bounded converter rather than JNI's modified UTF-8, so supplementary characters cannot overflow the DNS label budget.

**Native receiver (C).** Derived from the UxPlay AirPlay core through Wormhole Display:

- mDNS/service registration so the Mac's picker can see the receiver
- an HTTP control server for `/info`, `/server-info`, RTSP-style `OPTIONS`, `SETUP`, `RECORD`, `TEARDOWN`, `GET_PARAMETER`
- AES-CTR decryption of the video stream, with a streaming decryptor that carries the tail of a partial block between packets
- access-unit parsing and frame delivery into the Kotlin decode pipeline

**Video pipeline (Kotlin).** `VideoFrameQueue` buffers access units; `VideoRenderer` feeds them to `MediaCodec`, which decodes into the `SurfaceView`'s surface. H.264 is the default; HEVC is opt-in because decoder quality varies across devices. `StreamTelemetry` tracks FPS, bitrate, resolution and codec for the debug overlay.

## Protocol notes

- Discovery: `_raop._tcp` and `_airplay._tcp` records with TXT keys that reflect what this build actually supports. The `/info` endpoint returns `statusFlags` `0x44`, consistent with the advertised RAOP TXT fields.
- Audio is excluded by design. `ANNOUNCE` is rejected unconditionally with `501`, no RSA private key exists in the tree, and the legacy RAOP audio path is compiled out. This receiver is for screen video only.
- `SETUP` validates its inputs: `eiv` must be exactly 16 bytes, `ekey` exactly 72 bytes, the plist root must be a dictionary, `streams` must be an array when present, and malformed roots get `400` rather than a false success. Duplicate SETUP on a live stream is rejected instead of rekeying the decryptor under a running worker.
- The control server does not assume a request arrives in one packet: partial requests are framed across reads, with a deadline, and shutdown interrupts the read loop instead of joining a wedged socket forever.
- Custom receiver names are capped at 50 UTF-8 bytes, which leaves room for the RAOP `AABBCCDDEEFF@` prefix inside the 63-byte DNS label limit.

## Security decisions

- No private key material: the legacy RSA key source was removed and replaced with an inert stub, so the build cannot answer encrypted-audio handshakes even if a sender asks.
- No DRM paths. Ordinary screen interoperability only.
- Session key material is not written to logs.
- The mirrored surface is marked secure, so screenshots and screen recorders cannot capture mirrored content.
- No analytics, no accounts, no remote endpoints. The only network traffic is local discovery and the AirPlay session with your Mac.

## Build and toolchain

- Gradle wrapper, Android Gradle Plugin 8.9.2, Kotlin 2.1.20, Compose BOM 2025.04.01.
- NDK r27d with `-DANDROID_SUPPORT_FLEXIBLE_PAGE_SIZES=ON`, which is what makes every native library 16 KiB-aligned for newer Android page sizes.
- OpenSSL 3.0.16 and libplist 2.6.0 are built from pinned source tarballs and linked statically, with provenance and checksums recorded under `tools/`.
- `minSdk 29` because the vendored static libraries were built for API 29; `targetSdk 34`; arm64-v8a only.

## Tests

| Suite | What it actually proves |
|---|---|
| JVM unit tests (75) | Queue, renderer parsing, identity and name budget, display math, history, lifecycle leases, resource ownership |
| Native host tests | Mirror buffer parser and EOF/join behaviour, DMAP parsing |
| Native audit harnesses | Real AES-CTR streaming against a reference, fragmented request parsing, HTTP partial-request and shutdown deadlines, active rekey, DNS label boundaries, UTF-8 JNI budget |
| Production core protocol (40 assertions) | The real RAOP/HTTP/mDNS handlers under ASan/UBSan: ANNOUNCE rejection, OPTIONS, malformed SETUP, `/info` flags, TXT construction |
| APK alignment validator | Every ELF `PT_LOAD` and ZIP data offset at 16 KiB, plus `zipalign` and `apksigner` |
| Android instrumentation (6 classes) | Real framework display acquisition, initialization retry, Activity and service-first startup, duplicate-start leases, session teardown |

Host tests are not device or Mac interoperability proof. They are the reason the receiver survives malformed input; they say nothing about how a particular Mac behaves.
