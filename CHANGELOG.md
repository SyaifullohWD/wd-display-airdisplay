# Changelog

## 0.2.1-dev

Icon artwork finally renders at the authored scale.

- Root cause of the long icon saga: an adaptive icon is drawn on a 108dp canvas but a launcher shows the 72dp viewport, so artwork must be composed at 72/108 of the canvas. It had been placed at 94%, which made the mark render about 1.4x too large and look identical to the older, oversized artwork. The design was correct; the composition was not.
- Artwork now sits at the 72dp viewport with the surrounding ring filled by clamping to the tile's own edge pixels, so the gradient stays continuous to the mask edge with no seam.
- Verified on device: the launcher now shows the mark at roughly 55 to 60% of the tile width, matching the designer's master.

## 0.2.0-dev

Install identity moved to the WD Display name.

- `applicationId` is now `org.wddisplay.receiver`. The code package stays `org.pocketairdisplay.receiver` so native JNI symbols and the receiver core are untouched.
- Device startup validator updated for the split: install identity, code package and service component are now resolved separately.
- Test fixtures no longer hardcode the package name; they read it from the validator.

## 0.1.9-dev

Launcher entry moved to an activity alias so its icon is not served from a stale cache.

- The launcher component is now `org.pocketairdisplay.receiver.Launcher`, an activity alias targeting `MainActivity`. One UI Home keys its cached icon bitmap to the launcher component, so reinstalls, version bumps, resource renames and reboots all kept showing a previously cached icon. A new component name has no cache to hit.
- `MainActivity` keeps `exported=true` and loses only its launcher intent filter, so explicit `am start` and instrumentation runs still work.
- Also diagnosed during this: Samsung's "apply color palette to app icons" was enabled (`colortheme_app_icon=1`), which routes icons through the theme engine and caches the result. It is now off; re-enable it in Settings → Wallpaper and style if you want tinted icons.
- No changes to protocol, service, permissions or decoder behaviour.

## 0.1.7-dev

Icon rebuilt from the designer's updated master, which is the version actually shipped.

- The artwork now uses the designer's corrected scale: the mark occupies 56% × 45% of the tile with 19-28% padding, instead of the earlier 78% × 62% that crowded the edges.
- Adaptive composition changed with it. The artwork is composed at 94% of the 108dp canvas, so the mask crops only the expendable outer corners of the gradient rather than wrapping the art in a visible ring. The mark now reads at the same relative size as the legacy icon and every other launcher icon.
- Monochrome layer removed. The gradient tile and glass mark are the identity, so this app opts out of Android 13 themed-icon tinting and always shows the original artwork. The notification small icon is unaffected.
- The master is kept in the repo at `design/art/wd-display-master.png`, so the whole set regenerates with `python3 design/art/build_icons_from_master.py design/art/wd-display-master.png`.

## 0.1.5-dev

Icon set rebuilt from the designer's 1024×1024 master.

- The artwork is a full-bleed periwinkle gradient tile with a translucent glass W, so the background is part of the identity and the icon is composed rather than keyed out.
- Adaptive icon uses a safe composition: the artwork sits at the 72dp viewport inside the 108dp layer, and the ring around it is filled by clamping to the tile's own edge pixels. The gradient therefore runs continuously to the mask edge, with no seam, and the mark's intentional off-centre balance is preserved under every launcher mask.
- Regenerated: legacy launcher PNGs at 48, 72, 96, 144 and 192 with baked rounded corners, adaptive foreground, background and monochrome layers at 432, TV banners at 320×180 and 640×360, and a 512×512 store/README icon.
- Reproducible from the master: `design/art/build_icons_from_master.py`.

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
