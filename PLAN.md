# Pocket AirDisplay evidence-backed plan

Owner: @hermes (default), session 20260918_170647_0c1438. Created October 19, 2026.

## Required outcome
An unlimited, free Android video receiver listed in macOS Control Center > Screen Mirroring. Mac must offer and actually render a separate extended desktop. Phone hotspot with only the laptop and phone is the preferred topology. Browser streaming, a custom sender, audio-only AirPlay, USB-only and mirrored screens do not satisfy acceptance.

## Evidence and limits
See evidence/INVESTIGATION-REA.md and evidence/rea/command-index.json for exact commands, exit codes, hashes and donor revisions.
- FDH2/UxPlay 4e95a9ec013c52d8555d88dbc55abe346e94d56e: GPLv3 receiver reference; no protected Apple TV DRM video support (README lines 266+).
- jqssun/android-airplay-server e347ee51ff3cb164d6e758496a428e3ab9b1df02: GPLv3 Android UxPlay JNI + MediaCodec/SurfaceView receiver, Android 7+, explicit same-subnet operation. Submodules initially uninitialized; current toolchain needs differ from installed SDK.
- pgodlews/wormhole-display fc8261661bf7c29f1ca4e37795c221da5d542192: GPLv3 Android UxPlay port. README explicitly documents selecting Extended display in macOS Displays settings; Meta Portal hardware tested upstream, general Android phone compatibility untested. Architecture explicitly excludes AWDL.
- REA 4.0.1 import-reference-source succeeded on all three pinned source trees. It provides historical source inventories/hashes, not native decompilation or runtime protocol proof. Native engines unavailable. Archive inspection attempts failed with recorded exact errors; do not fabricate successful analysis.
- Actual local terminal access to requested directory works. Android Studio JBR 21 works; default java is a nonworking stub. SDK 36.1 and Build Tools 36 exist; NDK/CMake/Gradle distributions not initially installed. adb shows no connected phone.

## Architecture hypothesis to validate
Prefer the smallest auditable open-source Android receiver donor, not a from-scratch AirPlay protocol reimplementation. Initial donor preference is Wormhole because it includes explicit extended-display metadata and a small JNI/MediaCodec pipeline; jqssun is the general-phone alternate if its native core is easier to build and audit. Pin all sources and retain licenses.

Pipeline:
1. Android foreground receiver lifecycle and user-visible start/stop, network/interface diagnosis and multicast lock.
2. Native or Android mDNS advertisement for _airplay._tcp and, only if needed, _raop._tcp, with features/TXT values consistent with actually implemented capabilities. Do not advertise unsupported protected-media support.
3. HTTP/RTSP session /info and pairing/stream setup for ordinary user-controlled desktop video. Sender, not Android UI, chooses mirror vs extended desktop.
4. Native transport feeds compressed H.264 frames through JNI to Android MediaCodec and SurfaceView; prefer hardware decoding, bounded queues, keyframe/reconnection handling. Start with video; audio is not core acceptance and legacy audio can be excluded.
5. Listener/address selection supports infrastructure Wi-Fi and phone-hotspot interfaces when reachable. Hotspot mDNS isolation/routing is a physical test gate, not assumed. No AWDL claim.

## Gate 0: source and scope audit BEFORE donor implementation
The donors include PlayFair/FairPlay-named transport code and, in Wormhole, a legacy AirPort RSA private-key component. A component name alone does not establish that ordinary desktop transport implements protected-content DRM. Audit the actual ordinary-screen call path and document the distinction with exact files and upstream evidence.
- Absolutely no proprietary key extraction, copying known embedded proprietary private keys into our distributed build, AirScreen patching/payment bypass, or enabling protected media DRM circumvention.
- Exclude legacy RSA/audio paths and key material from any derived build where feasible. Do not run proprietary application extraction tools.
- If ordinary nonprotected screen interoperability cannot work without excluded material or requires prohibited bypass, STOP that integration path, record the exact dependency and mark primary acceptance blocked. Do not advertise a discovery-only app as a working receiver.
- Reuse only appropriately licensed open-source interoperability code and preserve notices/GPL source obligations. Do not claim formal legal clearance.

## Gate 1: bounded feasibility spike
Implementation specialist inspects native/JNI contracts, builds the smallest real receiver and exercises host-testable protocol endpoints. First prove discovery records and /info/session parsing against real code; synthetic clients are tests, not Mac acceptance. Run invalid/fragmented protocol tests and lifecycle tests where feasible. Do not spend the project on settings/UI polish.

## Gate 2: toolchain and APK
Use explicit JAVA_HOME=/Applications/Android Studio.app/Contents/jbr/Contents/Home and existing SDK. Local project-owned SDK/NDK/CMake/Gradle provisioning is allowed for the requested build; do not change shell profiles, system security, firewall or network settings. Record download sources/checksums and failures. Don't install paid tools or hidden dependencies. Prefer source builds to opaque donor prebuilts. Build debug APK; verify application id, ABI, manifest, signature, native library packaging and checksum with Android tools. Keep build scripts and complete raw logs. No phone installation without user authorization.

## Gate 3: device and travel acceptance
Explicit physical checks, currently unavailable:
- Authorized Android hardware runs APK, advertises expected receiver name; native Mac picker sees it.
- Connect using native Mac UI, choose Extended display, show separate windows/pointer on phone while Mac retains its own content. Record Mac display inventory and phone output; mirror-only is fail.
- Repeat while laptop joins Android phone hotspot; no router or custom Mac sender. Record actual interfaces/IPs/mDNS/connection failure if topology isolates clients.
- Disconnect/reconnect, background/foreground, rotation and 60-minute uninterrupted video session with no app-imposed timer/watermark/ads. This checks unlimited operation but cannot mathematically prove unlimited duration.
- Packet captures require explicit limited scope to our receiver traffic; no capture of unrelated personal traffic.

## Workstream contracts and ownership
- Hermes: orchestration, project plan, evidence review, independent verification and truthful status. Do not personally implement code.
- Evidence investigation specialist: completed evidence/INVESTIGATION-REA.md, pinned references and REA command captures.
- Implementation specialist: Claude Code Sonnet via claude-code skill, project-scoped native/Android code, tests, scripts, build logs and APK. Read BRIEF/PLAN before work; write evidence/SCOPE-AUDIT.md before integration. Can report hard blockers; cannot redefine acceptance or silently move project.
- Reviewer: read-only independent review of native lifecycle, memory ownership, advertised capabilities, licensing/prohibited-key exclusion and build evidence. No claim of hardware success.
- Durable board: pocket-airdisplay. Parent owner default/Hermes; tasks/IDs and continuation recorded in STATUS.md. Implementation success awaits host verification; overall goal remains open until physical acceptance or explicit blocked report.

## Required artifacts
README.md (build, run, native Mac usage, hotspot troubleshooting and honest limitations); PLAN.md; STATUS.md; evidence/SCOPE-AUDIT.md; source with pinned provenance and licenses; reproducible build/test commands and raw logs; deliverable APK if build succeeds. Every failure has an exact command/error and next owner/action. No empty JNI stubs represented as receiver functionality.
