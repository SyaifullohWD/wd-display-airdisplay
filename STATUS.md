# Pocket AirDisplay status

## Latest update: WD Display rebrand and Apple-style restyle installed

Supersedes the naming and appearance statements below. Behavior, protocol, service, permissions and lifecycle were not changed in this pass.

- Product name: user-visible branding is now **WD Display** everywhere (the app_name string already read WD Display, but the in-app header still said "Wormhole Display"; it is fixed). Internal package, class and JNI names intentionally unchanged.
- New mark: two mirrored right-angle strokes forming an italic W, drawn as a soft glass object on a dark tile. Full icon set regenerated (adaptive foreground/background/monochrome, legacy mipmaps mdpi..xxxhdpi, TV banners) plus the master SVG and deterministic generator under design/. Verified legible at 48dp, unclipped, alpha correct.
- UI: Compose presentation now resolves a single token layer in WdTheme.kt (appearance-resolved colors, spacing, radii, type ramp, grouped-card/row/section primitives). Apple-system grammar: grouped inset cards with hairline separators, leading-title rows with trailing controls, pill segmented control for screen orientation, hierarchical label colors, restrained translucency. Zero raw Color(0x...) literals remain in MainActivity.kt. Light and dark appearance both resolve. Information architecture unchanged.
- Verified: full host gate passes and published a coherent release (JVM 75 tests, native and production-core suites, native audit regressions, APK alignment and signature gates). On the authorized Galaxy A55: application and test APKs installed, device startup validator PASS (cold Activity and service-first), and all six instrumentation classes pass individually. Installed SHA256 equals the published release APK: 55f8574b79649a54b9144b492cf5e8628b2be4dce54b1b5372d0004a4c45538b, versionName 0.1.2-dev, versionCode 3. App relaunched and left running with its foreground service.
- Rendered-text evidence (accessibility hierarchy) confirms the new UI on device because screenshots are impossible here: the video surface sets FLAG_SECURE, so screencap returns stale frames. See evidence/ui-revamp/ and design/BRANDING-NOTES.md.
- Note for operators: the first host-gate run of this pass failed closed on a Python delivery-gate fixture that reported "NO TESTS RAN" for a stub suite; a re-run passed cleanly with identical inputs. Publication was correctly refused on the failing run, so no mixed release was created. Treat that fixture as a known flake candidate worth hardening.
- Still unverified: interactive notification allow/deny and background-recovery paths, wake-lock behavior under long idle, and every Mac-side acceptance item (native Screen Mirroring discovery, pairing, actual separate extended desktop, hardware decode, hotspot, sustained session).

## Latest update: audited fixes integrated; Galaxy A55 startup/lifecycle verified

This section supersedes historical progress and artifact identities below. Full report: `evidence/FIX-INTEGRATION-RESULT.md`.

- Fixed default version **0.1.1-dev / versionCode 2**; full `bash scripts/build.sh` passed with the actual JBR/project SDK/NDK. JVM **75/75**, native mirror **50 cases + DMAP**, production protocol **40/40**, mandatory AES/rekey/HTTP/DNS/JNI UTF-8 regressions, Python **33/33**, all-ELF/ZIP 16 KiB alignment, SDK zipalign and APK signature gates pass. Instrumentation APK actually compiled.
- Coherent final release: `.delivery-releases/release-c98b0e8514c0427ba81d2e784328d828/` (`deliverables` points here). APK SHA256 **d17d2f77dc25772308c860f1bd5ca194e9f16a9b39e37d33edbe35904096eb8e**; source SHA256 **337cb00be1930c82203caa3ee33697dfdcaa88f2c4c2af11dfea77ab353fd0ed**. All 321 source file members byte-match current source. Prior releases/evidence retained.
- User-authorized application and matching test APK updates succeeded on explicit **Galaxy A55 / SM-A556E / RRCX4021XSW / adb transport 1**. Pulled installed application/test hashes exactly match. Final validator cold Activity PID **7605 → 7605**, real foreground service/native listener and one service-first test pass; no fresh app crashes. Six classes each pass one real test in separate fresh processes; test fixture boot autostart preference restored byte-for-byte afterward.
- JNI standard UTF-8 accounting now matches Kotlin's 50-byte limit, preserving native rejection. The real service-first Unicode test uses 12 emoji + `xx`; no blanket Unicode restriction.
- The initial notification-permission dialog was a real blocker, not automatically granted/clicked. Later startup passed while POST_NOTIFICATIONS remained ungranted. Interactive allow/deny and denied-notification recovery remain **UNVERIFIED**; historical failed runs retained. No data wipe, security/overlay/network settings change or capture. The service test uses its disclosed temporary test shell FGS-start identity only.
- App left open and observed healthy, PID **8108 → 8108**, MainActivity top resumed, foreground service and fresh same-PID native listener; raw records `evidence/fix-integration/final-open-health-4/`.
- **Still open:** native Mac picker/connection/extended desktop, phone video decode, hotspot, reconnect/rotation and sustained runtime; interactive notification recovery; OS/OEM long-idle wake-lock acceptance; callback/reentrant shutdown risks, disabled-audio/cover-art hardening and protocol-size/fuzzing scope. No claim of completed Mac interoperability or 16 KiB-device runtime.

## Latest update: 16 KB alignment fixed and corrected APK installed

This section supersedes the earlier progress, artifact hashes and no-install statements below. The host build task has completed review. The user then explicitly authorized installation on the wireless-debugging Galaxy A55.

The first APK exposed a missed compatibility defect: libpocketairdisplay.so PT_LOAD alignment was 4096 bytes. A delegated specialist enabled NDK r27 flexible page sizes, added regression validation and rebuilt. Parent independently verified corrected APK: two ELF libraries, six PT_LOAD segments at 16384-byte alignment, 110 stored ZIP entries checked, zero failures. Corrected SHA256: cfd5e754d4a4444b0b42dcd192ac58b57dcc0265559b1d9a9d2581a4c832ae6a.

Parent installed the corrected APK with adb (Success), then read back the installed base.apk checksum on the phone: exact match. Warning disappearance and actual Mac native discovery/extended desktop/hotspot remain unverified. Phone reports 4096-byte runtime pages; real 16KB-device runtime is not tested. See evidence/16KB-ALIGNMENT-RESULT.md for evidence and temporary-directory provenance clarification.


Owner: @hermes (default profile), primary orchestrator.
Owning session: 20260918_170647_0c1438.
Handoff accepted: October 19, 2026, 07:22 WIB.
Workspace: /Users/syaifullohwd/Documents/Code/pocket-airdisplay.

## Access verified
- BRIEF.md read with read_file before investigation.
- This session's terminal successfully changed into the requested project directory and verified BRIEF.md readable and the directory writable. No macOS permission denial observed in this terminal.
- Project has not been moved.

## Scope and acceptance
1. Free/unlimited Android receiver, no paid runtime dependencies or payment/DRM bypass.
2. Discoverable in native macOS Control Center > Screen Mirroring.
3. Actual connection and separate extended desktop, not mirroring alone.
4. Phone-hotspot travel topology investigated and tested separately from AWDL.
5. Real APK plus exact build/test logs when toolchain permits.
6. Device acceptance requires authorized real Android hardware; compilation and simulated tests do not prove interoperability.

## Work underway
- REA/source investigation completed: evidence/INVESTIGATION-REA.md, pinned references/ and exact command records under evidence/rea/. Three historical-source imports succeeded; native decompilation is unavailable and not claimed.
- PLAN.md written before implementation; includes source/key scope audit, native protocol spike, real APK build and separate physical acceptance gates.
- Implementation delegated to Claude Code Sonnet (claude-sonnet-4-6), not written by the orchestrator. Worker starts by auditing prohibited material before donor integration.

## Confirmed inventory and blockers
- Android Studio JBR 21 works; /usr/bin/java is only a failing stub. SDK 36.1, Build Tools 36 and adb installed. SDK NDK/CMake/cmdline-tools initially absent; specialist can provision free project-owned build tools with provenance recorded.
- No Android device attached. Native Mac picker, actual extension, phone hotspot and sustained runtime remain UNTESTED.
- Donors include PlayFair-named transport and legacy RSA audio code; specialist must distinguish ordinary desktop transport from protected DRM and exclude proprietary key/legacy paths. No claim of legal clearance or protected-content support.
- REA doctor: Hopper/Ghidra missing and registrations absent. No paid analysis engines installed. Supported historical-source inventories work; archive inspection attempts failed with captured errors.

## Durable ownership and continuation
Board: pocket-airdisplay (default board selection unchanged).
Host build task: t_4e38b197, owner default/@hermes. Manual claim run #1 transferred to supported Kanban dispatcher after all three Sonnet phases exited. Runs #2/#3 could not orchestrate through the Claude relay: it returned `Error: Reached max turns (1)` with zero tool calls. Removed ONLY the task-specific model override; no global settings changed. Dispatcher run #4 now uses the profile's existing default runtime, PID 3889, verified running and issuing its first kanban_show tool call. It must continue delegating implementation to the same Claude Code Sonnet session.
Physical acceptance task: t_0ae61b6d, owner default/@hermes, blocked until authorized real device is available.

Implementation session: 17922c4c-4778-4fdd-9e9a-02c8ce7aa85d. Phases 1-3 each hit max-turns; that is NOT a build success. Phase1 produced evidence/SCOPE-AUDIT.md; phase2 produced the derived Android app source; phase3 applies native safety and capability fixes. Logs: evidence/implementation-sonnet.jsonl, implementation-sonnet-phase2.jsonl, implementation-sonnet-phase3.jsonl and matching stderr files. Independent reviewer findings: evidence/REVIEW-NOTES.md, including NULL-safe destruction, unconditional ANNOUNCE rejection, malformed SETUP validation, and distribution exclusion.

Current implementation status: derived app/ source exists (14MB observed); no APK, compiled native tests, Gradle build or hardware pass is yet claimed. Scope audit supports separating ordinary desktop transport from legacy proprietary RSA/audio material; actual derived source/artifact exclusion and operation must be tested. The reference snapshots are evidence only, not sanitized deliverables.

Next worker action is explicit in task comments: finish build config/licenses, provision project-local free toolchain, RUN actual native tests and Gradle APK build with raw logs; resume the SAME Sonnet session on bounded-turn exhaustion. No competing writers. Hermes dispatcher worker owns verification and task transitions; it may mark blocked only for a concrete documented hard blocker and never complete for an unbuilt scaffold. Read live status using `hermes kanban --board pocket-airdisplay show t_4e38b197` and logs using `hermes kanban --board pocket-airdisplay log t_4e38b197`. CLI has no guaranteed live push delivery, so do not promise this terminal will receive a notification after it closes.

Work contract: IMPLEMENTATION-WORKORDER.md. Worker must produce evidence/IMPLEMENTATION-RESULT.md and README.md, exact test/build results, and APK path if successful. No phone installation or security/network changes authorized. Entire product remains incomplete until physical acceptance, irrespective of host build progress.

## Verified host handoff, dispatcher run 4 (supersedes progress above)

- Host implementation and current-source debug APK built. Clean Gradle `clean :app:assembleDebug :app:testDebugUnitTest --no-build-cache --console=plain` exited 0. Parent verified 64 tests across 12 XML suites, all zero failures/errors.
- Real production-handler and discovery-TXT host harness passes 40 assertions with ASan/UBSan; network registration/workers are stubbed and no LAN advertising is required. Mirror receive-loop regression passes 50 cases plus DMAP parser test. These are host tests, not Android/Mac interoperability proof.
- OpenSSL 3.0.16 and libplist 2.6.0 rebuilt from recorded upstream source tarballs. Source/archive hashes independently matched provenance. Mandatory input hash checks now pinned. References remain read-only inputs and were independently git-clean when checked.
- Final APK: `/Users/syaifullohwd/Documents/Code/pocket-airdisplay/deliverables/pocket-airdisplay-debug.apk`, 28,909,990 bytes. SHA256 `f130d0ab290bae5ba0fa8eaaa8fb6d4cc7f6b85c4dd0e1a38a8174c61d56f8d5`. Parent verified it matches current Gradle output and Android debug signature. Package `org.pocketairdisplay.receiver`, label Pocket AirDisplay, arm64-v8a, minimum Android 10/API29, target34.
- Corresponding source bundle and SHA256SUMS are beside APK. No reference donor key file is distributed; derived rsakey implementation is inert and legacy ANNOUNCE rejected. Source/license provenance is documented, not formal legal clearance.
- Sonnet session `17922c4c-4778-4fdd-9e9a-02c8ce7aa85d` reached API429 in phase15. After it exited, one sequential fallback finished the real core harness and final packaging. No parallel writer, owner remains default/Hermes. Logs `evidence/implementation-fallback-core.jsonl` and `evidence/implementation-fallback-final.jsonl`.
- Operator verified Galaxy A55 wireless-debug connection. This only authorizes connection verification, not installation, launch, capture or network/security changes. No install/launch/capture performed. Separate physical task `t_0ae61b6d` requires explicit authorization.
- Native Mac picker, actual extension, on-device decoding, phone-hotspot operation and 60-minute continuous session remain UNTESTED. JNI callback/stop concurrency and stricter SETUP interoperability remain physical/review risks, not proven by host tests.
- README and `evidence/IMPLEMENTATION-RESULT.md` now distinguish implemented source, host proof and hardware gates. Host task submitted for review, not represented as completed product acceptance.

## Review round 2 (run 6) — documentation corrections, re-verified

Reviewer run 5 independently rebuilt and reproduced the exact APK SHA-256, then requested three documentation-level corrections (APK hash to remain unchanged). Run 6 applied all three, verified them, and re-requested review:

1. `THIRD_PARTY_NOTICES.md` added §2.1 declared and §2.2 resolved (85-module) Maven dependency tables with pinned versions, licenses and shipped/test-only/build-only scope. Versions taken from live Gradle resolution, not memory.
2. The dead `references/...` link in the notices was replaced with the upstream file pinned at commit `fc8261661bf7c29f1ca4e37795c221da5d542192` (HTTP 200 verified) plus a self-contained inline patch inventory separating carried patches from the deliberately excluded legacy RSA/RAOP-audio patches. Source bundle + `SHA256SUMS` regenerated.
3. Test sources moved to `app/src/test/java/org/pocketairdisplay/receiver/` to match the `package org.pocketairdisplay.receiver` declaration (package itself unchanged; the earlier package-rename attempt that failed to compile is preserved in the build logs).

Re-verification in run 6: clean Gradle `assembleDebug` + `testDebugUnitTest` exit 0 with the rebuilt APK SHA-256 byte-identical to the delivered one (`f130d0ab…`); 12 suites / 64 tests / 0 failures; `test-native.sh` 50 cases + dmap exit 0; `test-core-protocol.sh` 40/40 exit 0; bundle rebuilt to 302 members with no excluded paths and no key markers. New source-bundle SHA-256 `d9b50846c3cd62f805749e4238c2e2edc98b000118b755a00aa9363b9037d003`. New `scripts/package-source.sh` makes the bundle reproducible. No native/Kotlin source change, no device install/launch, no network/security change. Physical acceptance remains blocked card `t_0ae61b6d`.

