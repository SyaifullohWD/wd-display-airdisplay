# Third-party notices

Pocket AirDisplay is a modified (derived) version of Wormhole Display, Copyright
© 2026 Piotr Godlewski, licensed under the GNU General Public License v3.0 (see
[LICENSE](LICENSE)). It includes the following third-party components, which
remain under their own copyrights and licenses.

## 1. Vendored native components

| Component | Version | License | Location | Upstream |
|---|---|---|---|---|
| UxPlay mirroring core (RPiPlay-derived) | vendored, with local patches (see §1.1) | [GPL-3.0](app/src/main/cpp/uxplay/LICENSE.GPLv3); `lib/` core LGPL-2.1-or-later | `app/src/main/cpp/uxplay/` | https://github.com/FDH2/UxPlay |
| llhttp (bundled with UxPlay) | vendored | MIT | `app/src/main/cpp/uxplay/lib/llhttp/` | https://github.com/nodejs/llhttp |
| mdnsd (bundled with UxPlay) | vendored | BSD-style | `app/src/main/cpp/uxplay/lib/mdnsd/` | via UxPlay |
| OpenSSL `libcrypto` (prebuilt static library + headers, arm64) | 3.0.16 | [Apache-2.0](app/src/main/cpp/deps/openssl/LICENSE.txt) | `app/src/main/cpp/deps/openssl/` | https://www.openssl.org/ |
| libplist (prebuilt static library + header, arm64) | 2.6.0 | [LGPL-2.1-or-later](app/src/main/cpp/deps/plist/COPYING.LESSER) | `app/src/main/cpp/deps/plist/` | https://github.com/libimobiledevice/libplist |

Per-file copyright and license headers in the vendored sources remain
authoritative. Full license texts are linked in the table. The OpenSSL and
libplist texts are the upstream files from the `openssl-3.0.16` and `2.6.0`
release tags.

### 1.1 UxPlay vendor-patch inventory for this derived build

The upstream inventory this tree derives from is
[`docs/uxplay-patches.md`](https://github.com/pgodlews/wormhole-display/blob/fc8261661bf7c29f1ca4e37795c221da5d542192/docs/uxplay-patches.md)
(Wormhole Display, pinned at commit `fc8261661bf7c29f1ca4e37795c221da5d542192`).
The inventory is summarised here so this notice is self-contained; the
`references/` donor checkouts are development inputs and are **not** part of the
distributed corresponding-source bundle.

Patches carried into `app/src/main/cpp/uxplay/lib/` by this derived build:

| File | Change |
|---|---|
| `raop.c` / `raop.h` | `raop_get_pk_str` public-key getter; partial-initialization shutdown guard (no `httpd_stop(NULL)`). |
| `raop_rtp_mirror.c` | H.264/HEVC parameter-set bounds checks; clear previous prepend state before replacing configuration; validate AVCC length/header availability before reads; allocation cap; EOF/allocation/streaming-report cleanup; worker-join ownership (the mirror worker no longer stops/joins itself). |
| `httpd.c` | Join a finished but unjoined worker before freeing it. |
| `byteutils.c` | Alignment-safe (`memcpy`) packet field loads/stores. |
| `mdnsd/dnssd_mdnsd.c` | Build a unique mDNS hostname from `hwaddr` instead of `gethostname()`, which returns "localhost" on Android. |

Patches from the upstream inventory that are **deliberately excluded** from this
derived build (legacy RAOP / "AirTunes" RSA audio, which is not protected-content
DRM and is unrelated to ordinary screen-transport encryption):

| Excluded upstream change | Reason |
|---|---|
| `rsakey.c` / `rsakey.h` (AirPort Express RSA key; Apple-Challenge signing, RSA-OAEP key unwrap) | The derived tree replaces this file with an inert, NULL-returning stub. No RSA private key material is present in the source tree or in the built `libpocketairdisplay.so`. |
| `raop_handlers.h`: `raop_handler_announce` (SDP parse, RSA-OAEP AES key, ALAC fmtp) and the legacy Transport-header branch of `raop_handler_setup` | `ANNOUNCE` is rejected unconditionally with `501` and mutates no state. |
| `raop.c` / `raop.h`: `Apple-Challenge`→`Apple-Response` handling, `rsakey` field, legacy `audio_running` callback | Removed with the RSA path; no legacy audio session is accepted. |
| `dnssdint.h` / `mdnsd/dnssd_mdnsd.c`: advertise `et=0,1`, `ek=1` and `am=AirPort4,107` | Advertised RAOP capabilities no longer claim the excluded legacy audio support. |

## 2. Android/JVM (Maven) dependencies

The debug APK packages Kotlin/Java bytecode from the Maven artifacts below.
Versions are the **resolved** versions from
`./gradlew --no-build-cache :app:dependencies --configuration debugRuntimeClasspath`
(Android Gradle Plugin dependency resolution, 2026-10-19). `Scope` states whether
the artifact is shipped in the APK, test-only, or build-only.

### 2.1 Declared dependencies

| Artifact | Version | License | Scope |
|---|---|---|---|
| `androidx.compose:compose-bom` | 2025.04.01 | Apache-2.0 | shipped (BOM, no code) |
| `androidx.compose.material3:material3` | 1.3.2 (via BOM) | Apache-2.0 | shipped |
| `androidx.compose.ui:ui` | 1.8.0 (via BOM) | Apache-2.0 | shipped |
| `androidx.compose.ui:ui-tooling-preview` | 1.8.0 (via BOM) | Apache-2.0 | shipped |
| `androidx.activity:activity-compose` | 1.10.1 | Apache-2.0 | shipped |
| `org.jetbrains.kotlin:kotlin-stdlib` (Kotlin runtime) | 2.1.20 | Apache-2.0 | shipped |
| `junit:junit` | 4.13.2 | EPL-1.0 | test-only |
| `com.android.tools.build:gradle` (Android Gradle Plugin) | 8.9.2 | Apache-2.0 | build-only |
| `org.jetbrains.kotlin:kotlin-gradle-plugin` (+ `kotlin.plugin.compose`) | 2.1.20 | Apache-2.0 | build-only |

### 2.2 Resolved transitive dependencies shipped in the APK

85 modules resolve on `debugRuntimeClasspath`. All are Apache-2.0 except where
noted; the full resolved set follows.

| Artifact | Version | License | Scope |
|---|---|---|---|
| `androidx.activity:activity` | 1.10.1 | Apache-2.0 | shipped |
| `androidx.activity:activity-ktx` | 1.10.1 | Apache-2.0 | shipped |
| `androidx.annotation:annotation` | 1.9.1 | Apache-2.0 | shipped |
| `androidx.annotation:annotation-experimental` | 1.4.1 | Apache-2.0 | shipped |
| `androidx.annotation:annotation-jvm` | 1.9.1 | Apache-2.0 | shipped |
| `androidx.arch.core:core-common` | 2.2.0 | Apache-2.0 | shipped |
| `androidx.arch.core:core-runtime` | 2.2.0 | Apache-2.0 | shipped |
| `androidx.autofill:autofill` | 1.0.0 | Apache-2.0 | shipped |
| `androidx.collection:collection` | 1.5.0 | Apache-2.0 | shipped |
| `androidx.collection:collection-jvm` | 1.5.0 | Apache-2.0 | shipped |
| `androidx.collection:collection-ktx` | 1.5.0 | Apache-2.0 | shipped |
| `androidx.compose.animation:animation` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.animation:animation-android` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.animation:animation-core` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.animation:animation-core-android` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.foundation:foundation` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.foundation:foundation-android` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.foundation:foundation-layout` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.foundation:foundation-layout-android` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.material3:material3-android` | 1.3.2 | Apache-2.0 | shipped |
| `androidx.compose.material:material-icons-core` | 1.7.8 | Apache-2.0 | shipped |
| `androidx.compose.material:material-icons-core-android` | 1.7.8 | Apache-2.0 | shipped |
| `androidx.compose.material:material-ripple` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.material:material-ripple-android` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.runtime:runtime` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.runtime:runtime-android` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.runtime:runtime-saveable` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.runtime:runtime-saveable-android` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.ui:ui-android` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.ui:ui-geometry` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.ui:ui-geometry-android` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.ui:ui-graphics` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.ui:ui-graphics-android` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.ui:ui-text` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.ui:ui-text-android` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.ui:ui-tooling-preview-android` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.ui:ui-unit` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.ui:ui-unit-android` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.ui:ui-util` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.compose.ui:ui-util-android` | 1.8.0 | Apache-2.0 | shipped |
| `androidx.concurrent:concurrent-futures` | 1.1.0 | Apache-2.0 | shipped |
| `androidx.core:core` | 1.13.1 | Apache-2.0 | shipped |
| `androidx.core:core-ktx` | 1.13.1 | Apache-2.0 | shipped |
| `androidx.core:core-viewtree` | 1.0.0 | Apache-2.0 | shipped |
| `androidx.customview:customview-poolingcontainer` | 1.0.0 | Apache-2.0 | shipped |
| `androidx.emoji2:emoji2` | 1.4.0 | Apache-2.0 | shipped |
| `androidx.graphics:graphics-path` | 1.0.1 | Apache-2.0 | shipped |
| `androidx.interpolator:interpolator` | 1.0.0 | Apache-2.0 | shipped |
| `androidx.lifecycle:lifecycle-common` | 2.8.7 | Apache-2.0 | shipped |
| `androidx.lifecycle:lifecycle-common-java8` | 2.8.7 | Apache-2.0 | shipped |
| `androidx.lifecycle:lifecycle-common-jvm` | 2.8.7 | Apache-2.0 | shipped |
| `androidx.lifecycle:lifecycle-livedata-core` | 2.8.7 | Apache-2.0 | shipped |
| `androidx.lifecycle:lifecycle-process` | 2.8.7 | Apache-2.0 | shipped |
| `androidx.lifecycle:lifecycle-runtime` | 2.8.7 | Apache-2.0 | shipped |
| `androidx.lifecycle:lifecycle-runtime-android` | 2.8.7 | Apache-2.0 | shipped |
| `androidx.lifecycle:lifecycle-runtime-compose` | 2.8.7 | Apache-2.0 | shipped |
| `androidx.lifecycle:lifecycle-runtime-compose-android` | 2.8.7 | Apache-2.0 | shipped |
| `androidx.lifecycle:lifecycle-runtime-ktx` | 2.8.7 | Apache-2.0 | shipped |
| `androidx.lifecycle:lifecycle-runtime-ktx-android` | 2.8.7 | Apache-2.0 | shipped |
| `androidx.lifecycle:lifecycle-viewmodel` | 2.8.7 | Apache-2.0 | shipped |
| `androidx.lifecycle:lifecycle-viewmodel-android` | 2.8.7 | Apache-2.0 | shipped |
| `androidx.lifecycle:lifecycle-viewmodel-ktx` | 2.8.7 | Apache-2.0 | shipped |
| `androidx.lifecycle:lifecycle-viewmodel-savedstate` | 2.8.7 | Apache-2.0 | shipped |
| `androidx.profileinstaller:profileinstaller` | 1.4.0 | Apache-2.0 | shipped |
| `androidx.savedstate:savedstate` | 1.2.1 | Apache-2.0 | shipped |
| `androidx.savedstate:savedstate-ktx` | 1.2.1 | Apache-2.0 | shipped |
| `androidx.startup:startup-runtime` | 1.1.1 | Apache-2.0 | shipped |
| `androidx.tracing:tracing` | 1.0.0 | Apache-2.0 | shipped |
| `androidx.versionedparcelable:versionedparcelable` | 1.1.1 | Apache-2.0 | shipped |
| `com.google.guava:listenablefuture` | 1.0 | Apache-2.0 | shipped |
| `org.jetbrains.kotlin:kotlin-stdlib-common` | 2.1.20 | Apache-2.0 | shipped |
| `org.jetbrains.kotlin:kotlin-stdlib-jdk7` | 1.8.20 | Apache-2.0 | shipped |
| `org.jetbrains.kotlin:kotlin-stdlib-jdk8` | 1.8.20 | Apache-2.0 | shipped |
| `org.jetbrains.kotlinx:kotlinx-coroutines-android` | 1.7.3 | Apache-2.0 | shipped |
| `org.jetbrains.kotlinx:kotlinx-coroutines-bom` | 1.7.3 | Apache-2.0 | shipped (BOM, no code) |
| `org.jetbrains.kotlinx:kotlinx-coroutines-core` | 1.7.3 | Apache-2.0 | shipped |
| `org.jetbrains.kotlinx:kotlinx-coroutines-core-jvm` | 1.7.3 | Apache-2.0 | shipped |
| `org.jetbrains:annotations` | 23.0.0 | Apache-2.0 | shipped |
| `org.jspecify:jspecify` | 1.0.0 | Apache-2.0 | shipped |

Test-only runtime additions (`debugUnitTestRuntimeClasspath`) resolve
`junit:junit:4.13.2` (EPL-1.0) with its `hamcrest-core:1.3` (BSD-3-Clause)
transitive dependency; neither is packaged in the APK. The Android Gradle Plugin
8.9.2 and Kotlin Gradle plugin 2.1.20 that perform the build are Apache-2.0 and
are likewise not packaged.

## 3. Native dependency provenance

The OpenSSL and libplist static libraries are built from unmodified upstream
release tarballs by `scripts/build-deps.sh` using the project-local NDK r27d
(aarch64-linux-android, api=29). Provenance and output checksums are recorded
in `tools/build-deps-provenance.txt` after each build run. Verified source
archive SHA256 checksums (recorded 2026-10-19):

| Library | Source archive SHA256 | Output .a SHA256 |
|---|---|---|
| OpenSSL 3.0.16 | `57e03c50feab5d31b152af2b764f10379aecd8ee92f16c985983ce4a99f7ef86` | `87a1ba3020e5653cd00e14256bbd49e945a87aaed3f215a7250443720fdd3e8d` |
| libplist 2.6.0 | `67be9ee3169366589c92dc7c22809b90f51911dd9de22520c39c9a64fb047c9c` | `661a3a3b55e11216f16e4624d9d9cd8e05f17ea37c88f2dc6102a1f69f93b44d` |

Both archives contain zero `/Users/` path references (verified with `strings | grep /Users/`).
