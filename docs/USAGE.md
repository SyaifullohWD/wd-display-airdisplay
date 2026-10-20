# Using WD Display

## The basic flow

1. Phone and Mac join the **same Wi-Fi network**. Home router, office Wi-Fi, or the phone's own hotspot all work in principle; the app relies on local multicast discovery.
2. Open **WD Display** on the phone. The status card shows **Ready to Connect**.
3. On the Mac, open **Control Center → Screen Mirroring**.
4. Pick **WD Display** (or whatever name you set).
5. The phone displays the Mac's screen.

There is nothing to install or configure on the Mac. The Mac treats the phone as an AirPlay display.

## Mirror or extended display

The Mac decides which mode you get, not the app:

- **Mirror**: same image on both screens.
- **Extended**: the phone becomes a second desktop with its own space.

To change it while connected: **System Settings → Displays** on the Mac, then choose how the WD Display screen is used. In extended mode you can move windows onto it and set the phone's position relative to the Mac's display.

Extended desktop is the least verified part of this project. It is implemented through the standard AirPlay display handshake, and the Mac controls it, but it has not been validated as a reliable standalone second workspace on real hardware. Test it before you depend on it for work.

## Settings, in order of usefulness

| Setting | What it does |
|---|---|
| **Screen Orientation** | Landscape, Portrait, or Auto (from the phone's tilt sensor). Pick the one that matches how you prop the phone up. Auto is only offered on devices with an orientation sensor. |
| **Speaker Output** | Play the stream's audio through the phone's speakers. Audio support is intentionally limited in this build; screen video is the supported path. |
| **H.265 video (Experimental)** | Lets compatible senders negotiate HEVC. Off by default. Turn it on only if H.264 looks poor on your phone. Reconnect after changing it. |
| **Telemetry Overlay (Debug)** | Draws live FPS, bitrate, resolution and codec in the corner of the mirrored image. Useful when judging whether the phone or the network is the bottleneck. |
| **Run in Background** | Keeps the receiver discoverable and connected when the app is not in front. Turning it off stops the receiver when you leave the app. |
| **Auto-open on connect** | Brings the app forward when a Mac starts streaming. Needs overlay access; without it you tap the notification instead. |
| **Start on Boot** | Starts the receiver when the phone powers on. |
| **Bonjour Service Name** | The name your Mac shows in the picker. Use something short and unique on a shared network, and avoid emoji if other devices have trouble discovering it. |

**Recent Connections** lists the last 10 sessions with the sender's name, how long it ran, the resolution and the codec. It is a local log stored on the phone only.

## Good habits for a stable second screen

- Keep the phone on a charger for long sessions. A receiver plus screen at full brightness drains a battery quickly.
- Prefer 5 GHz if your router splits bands. Video bitrate is far more stable there.
- Turn off battery optimization for WD Display (Android Settings → Apps → WD Display → Battery → Unrestricted). Aggressive OEM power management is the most common reason a receiver stops advertising when idle.
- If you rename the receiver, reconnect from the Mac afterwards. The picker caches names.
- Do not put the phone in a place where it will lock and sleep mid-session; the receiver keeps a wake lock while running, but the screen itself should stay on for video.

## Network requirements

- Both devices must be on the same subnet.
- Client isolation or "AP isolation" on guest Wi-Fi blocks discovery. Use the main network.
- VPNs on either device can break multicast. Turn them off while connecting.
- mDNS does not cross NAT boundaries, so a phone on cellular data will never appear to a Mac on Wi-Fi.
- Apple's peer-to-peer AWDL link is not implemented. Discovery requires a shared network or hotspot.

## Privacy

Screen content is delivered directly from your Mac to your phone over the local network. Nothing is uploaded, recorded or relayed through a server. The app has no analytics, no account system and no internet endpoint.

The mirrored video surface is marked secure, so Android screenshots and screen recorders cannot capture it.

## Known limitations

- 32-bit phones are not supported.
- Audio-only AirPlay (Apple Music to a receiver) is not supported. Legacy RAOP audio is deliberately excluded.
- DRM-protected content from Apple's TV app will not play; this build does not implement protected-content paths.
- No AWDL, so no router-free peer-to-peer mode.
- H.265 support depends on the phone's hardware decoder.
- Renaming, restart and history are local app features only. Nothing syncs between devices.
