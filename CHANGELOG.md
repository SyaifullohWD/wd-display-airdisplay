# Changelog

## 0.1.4-dev

Apple-style visual language, and the layout no longer collapses on phones.

- Density is now chosen from screen **width** instead of height. A phone in landscape used to fall into the cramped TV tier, which produced 8dp page padding, 5dp card gaps and 10-12sp text. That was the tight, airless layout people complained about.
- Comfortable spacing throughout: 20-24dp page insets, 16dp card padding, 16dp section gaps, 12dp divider spacing, row heights around 52dp.
- Type scale raised: 34sp large title, 18-20sp section headers, 15-17sp row labels, 13sp supporting text.
- Status redesigned. The floating pill chip is gone; status is now a grouped card with a state dot, the status line and the Screen Mirroring instruction as its secondary line.
- iOS system palette. Pure black page, gray grouped cards, system blue tint, system green switches, hairline separators and the iOS label hierarchy (primary, secondary, tertiary), in both light and dark appearance.
- Fixed the widget that forced unused vertical space in the status area.

## 0.1.3-dev

First genuinely different palette: pure black page, iOS gray cards, system blue accent, green switches.

## 0.1.2-dev

Theming groundwork and full identity asset set.

- All UI colors and type sizes moved into a single token layer (`WdTheme.kt`). No color literals remain in the UI code.
- Grouped card, row and section header primitives added.
- Pill segmented control for screen orientation.
- New app mark: two mirrored right-angle strokes forming an italic W, rendered as a soft glass object on a dark tile.
- Full launcher icon set: adaptive foreground, background and monochrome variants, all legacy densities, plus the TV banner.
- Renamed the product to **WD Display** everywhere it is user-visible. Internal package, class and JNI names deliberately unchanged.

## 0.1.1-dev

Correctness and safety pass after a full audit.

- Startup crash fixed: display metrics were read from an application context, which Android rejects. The receiver now resolves the display through the display manager, and initialization is only marked complete when it actually succeeds.
- Background mode off now actually stops the receiver when the app is minimized.
- Notification permission requested properly; full-screen intent removed because a low-importance channel cannot legally use one.
- Receiver names capped at 50 UTF-8 bytes so the generated DNS label stays under the 63-byte limit.
- Session history is recorded on explicit teardown instead of being silently dropped.
- Audio decoder allocation failure no longer leaks a codec instance.
- Portrait 2:3 displays classified correctly.
- Native hardening: AES-CTR streaming tail handling fixed (out-of-bounds write on short packets), duplicate stream SETUP can no longer rekey a live decryptor, partial HTTP requests have a deadline and shutdown interrupts the read loop, request URLs can no longer over-read across a fragmented buffer, and DNS registration reports failure instead of pretending to succeed.
- 16 KiB ELF and ZIP alignment fixed via the NDK r27 flexible page size flag, with a regression gate that fails the build if any load segment drifts.
- Delivery pipeline rebuilt around staged publication: a failing gate retains the previous release instead of publishing a mixed APK and source.

## 0.1.0

Initial working receiver.

- AirPlay receiver for Android that appears in the macOS Screen Mirroring picker, derived from Wormhole Display and the UxPlay core.
- H.264 decode through MediaCodec into a SurfaceView, optional HEVC.
- mDNS registration, `/info`, and the RTSP-style control surface a Mac needs.
- Legacy RAOP audio excluded: no RSA private key in the tree, ANNOUNCE rejected.
- Foreground receiver service, wake lock, start on boot, connection history, telemetry overlay.
