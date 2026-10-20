#!/bin/bash
# Rebuild libcrypto (OpenSSL 3.0.16) and libplist-2.0 (libplist 2.6.0) for
# android-arm64 using the project-local NDK. Outputs go to app/src/main/cpp/deps/.
#
# Pinned source tarballs with MANDATORY expected SHA256 checksums (defined
# below). Both tarballs are verified against the pins before any extraction;
# a mismatch aborts the build. Outputs are also checksummed for provenance.
# Requires: .tools/ndk-r27d at repo root (NDK 27.3.13750724).
#
# Usage:
#   ./scripts/build-deps.sh
#
# Adapated from references/wormhole-display/scripts/build-deps.sh (GPLv3).
set -euo pipefail

repo_dir="$(cd "$(dirname "$0")/.." && pwd)"
tools="$repo_dir/tools"
ndk="$repo_dir/.tools/ndk-r27d"
out="$repo_dir/app/src/main/cpp/deps"
api=29
host=aarch64-linux-android
cpus="$(sysctl -n hw.ncpu 2>/dev/null || nproc)"

# Pinned source URLs and mandatory expected SHA256 checksums. Both tarballs are
# verified against these pins BEFORE extraction; a mismatch aborts the build.
OPENSSL_URL="https://github.com/openssl/openssl/releases/download/openssl-3.0.16/openssl-3.0.16.tar.gz"
PLIST_URL="https://github.com/libimobiledevice/libplist/releases/download/2.6.0/libplist-2.6.0.tar.bz2"
OPENSSL_SHA256_PIN="57e03c50feab5d31b152af2b764f10379aecd8ee92f16c985983ce4a99f7ef86"
PLIST_SHA256_PIN="67be9ee3169366589c92dc7c22809b90f51911dd9de22520c39c9a64fb047c9c"
PROVENANCE="$repo_dir/tools/build-deps-provenance.txt"

if [ ! -d "$ndk" ]; then
    echo "ERROR: NDK not found at $ndk" >&2
    echo "Download from: https://dl.google.com/android/repository/android-ndk-r27d-darwin.zip" >&2
    echo "SHA1: 2970926d705988f79baa9b04c51b4f7914dd8c56" >&2
    exit 1
fi

mkdir -p "$tools"

# Download sources if not already cached. A cached tarball that does not match
# its pin is deleted and re-fetched once; a failed pin check aborts below.
fetch_pinned() {
    url="$1"; dest="$2"; pin="$3"; name="$4"
    if [ -f "$dest" ]; then
        have="$(shasum -a 256 "$dest" | awk '{print $1}')"
        if [ "$have" = "$pin" ]; then return 0; fi
        echo "Cached $name SHA256 mismatch ($have != pin $pin); re-fetching..."
        rm -f "$dest"
    fi
    curl -fL -o "$dest" "$url"
}
fetch_pinned "$OPENSSL_URL" "$tools/openssl.tar.gz" "$OPENSSL_SHA256_PIN" "openssl-3.0.16.tar.gz"
fetch_pinned "$PLIST_URL" "$tools/libplist.tar.gz" "$PLIST_SHA256_PIN" "libplist-2.6.0.tar.bz2"

# Compute actual checksums.
OPENSSL_SHA256="$(shasum -a 256 "$tools/openssl.tar.gz" | awk '{print $1}')"
PLIST_SHA256="$(shasum -a 256 "$tools/libplist.tar.gz" | awk '{print $1}')"

echo "OpenSSL 3.0.16 SHA256:  $OPENSSL_SHA256 (pin $OPENSSL_SHA256_PIN)"
echo "libplist 2.6.0  SHA256:  $PLIST_SHA256 (pin $PLIST_SHA256_PIN)"

# Mandatory pin verification BEFORE any extraction.
if [ "$OPENSSL_SHA256" != "$OPENSSL_SHA256_PIN" ]; then
    echo "ERROR: openssl-3.0.16.tar.gz SHA256 mismatch: expected $OPENSSL_SHA256_PIN, got $OPENSSL_SHA256" >&2
    exit 1
fi
if [ "$PLIST_SHA256" != "$PLIST_SHA256_PIN" ]; then
    echo "ERROR: libplist-2.6.0.tar.bz2 SHA256 mismatch: expected $PLIST_SHA256_PIN, got $PLIST_SHA256" >&2
    exit 1
fi

# Write provenance record.
cat > "$PROVENANCE" << EOF
build-deps provenance — $(date -u +%Y-%m-%dT%H:%M:%SZ)

openssl-3.0.16.tar.gz
  url:    $OPENSSL_URL
  sha256: $OPENSSL_SHA256
  pinned: $OPENSSL_SHA256_PIN (verified before extraction)

libplist-2.6.0.tar.bz2
  url:    $PLIST_URL
  sha256: $PLIST_SHA256
  pinned: $PLIST_SHA256_PIN (verified before extraction)

NDK: $ndk
NDK revision: $(cat "$ndk/source.properties" | grep Pkg.Revision | cut -d= -f2 | tr -d ' ')
api: $api
host triple: $host
build host: $(uname -srm)
EOF
echo "Provenance written to: $PROVENANCE"

# Extract sources fresh each time.
rm -rf "$tools/openssl-3.0.16" "$tools/libplist-2.6.0" "$tools/libplist-install"
echo "Extracting sources..."
tar xf "$tools/openssl.tar.gz" -C "$tools"
tar xf "$tools/libplist.tar.gz" -C "$tools"
openssl_src="$tools/openssl-3.0.16"
plist_src="$tools/libplist-2.6.0"

tc="$ndk/toolchains/llvm/prebuilt/darwin-x86_64/bin"

# --- OpenSSL 3.0.16: static libcrypto only ---
# OpenSSL 3.0 requires ANDROID_NDK_ROOT (not ANDROID_NDK_HOME).
export ANDROID_NDK_HOME="$ndk"
export ANDROID_NDK_ROOT="$ndk"
export PATH="$tc:$PATH"
echo ""
echo "Building OpenSSL 3.0.16 libcrypto (android-arm64, api=$api)..."
cd "$openssl_src"
./Configure android-arm64 -D__ANDROID_API__=$api \
    no-shared no-tests no-ui-console \
    2>&1
make -j"$cpus" build_libs 2>&1
mkdir -p "$out/openssl/lib/arm64-v8a" "$out/openssl/include"
cp libcrypto.a "$out/openssl/lib/arm64-v8a/"
cp -r include/openssl "$out/openssl/include/"
LIBCRYPTO_SHA256="$(shasum -a 256 "$out/openssl/lib/arm64-v8a/libcrypto.a" | awk '{print $1}')"
echo "libcrypto.a SHA256: $LIBCRYPTO_SHA256"

# --- libplist 2.6.0: static C library via autotools ---
# The 2.6.0 release tarball is autotools-only (no CMake).
# 'make install' can fail on ranlib PATH lookup after archive install — run llvm-ranlib manually.
echo ""
echo "Building libplist 2.6.0 (android-arm64, api=$api)..."
cd "$plist_src"
./configure \
    --host=$host \
    CC="$host$api-clang" \
    CXX="$host$api-clang++" \
    AR=llvm-ar \
    RANLIB=llvm-ranlib \
    STRIP=llvm-strip \
    --disable-shared --enable-static \
    --without-cython --without-tests \
    --prefix="$tools/libplist-install" \
    2>&1
make -j"$cpus" 2>&1
# 'make install' can fail on ranlib PATH lookup after the archive is installed.
# Failure is NEVER ignored as `|| true`: it is tolerated only below, after
# llvm-ranlib is run manually AND the installed files are proven valid.
install_status=0
make install 2>&1 || install_status=$?
if [ $install_status -ne 0 ]; then
    echo "WARNING: 'make install' exited $install_status; attempting documented llvm-ranlib repair path"
fi
# Ensure ranlib finishes the archive even if make install failed at ranlib.
"$tc/llvm-ranlib" "$tools/libplist-install/lib/libplist-2.0.a"
# Strip local build paths from DWARF so committed .a is reproducible.
"$tc/llvm-strip" --strip-debug "$tools/libplist-install/lib/libplist-2.0.a"
# Validate installed outputs: required files present, archive is a readable ar
# library with members, and headers were installed. Abort on any failure.
plist_lib="$tools/libplist-install/lib/libplist-2.0.a"
plist_hdr="$tools/libplist-install/include/plist/plist.h"
for f in "$plist_lib" "$plist_hdr"; do
    if [ ! -f "$f" ]; then
        echo "ERROR: required libplist output missing after make install (exit $install_status): $f" >&2
        exit 1
    fi
done
members="$("$tc/llvm-ar" t "$plist_lib" 2>/dev/null || true)"
if [ -z "$members" ]; then
    echo "ERROR: $plist_lib is not a valid ar archive (make install exit $install_status)" >&2
    exit 1
fi
echo "libplist install OK (make install exit $install_status, $(echo "$members" | wc -l | tr -d ' ') archive members)"
mkdir -p "$out/plist/lib/arm64-v8a" "$out/plist/include/plist"
cp "$tools/libplist-install/lib/libplist-2.0.a" "$out/plist/lib/arm64-v8a/"
cp "$plist_src/include/plist/plist.h" "$out/plist/include/plist/"
LIBPLIST_SHA256="$(shasum -a 256 "$out/plist/lib/arm64-v8a/libplist-2.0.a" | awk '{print $1}')"
echo "libplist-2.0.a SHA256: $LIBPLIST_SHA256"

# Append output artifact checksums to provenance.
cat >> "$PROVENANCE" << EOF

output artifacts (arm64-v8a):
  libcrypto.a  sha256: $LIBCRYPTO_SHA256
  libplist-2.0.a sha256: $LIBPLIST_SHA256

verify source output is path-clean:
  strings -a $out/openssl/lib/arm64-v8a/libcrypto.a | grep /Users/ | wc -l   # expect 0
  strings -a $out/plist/lib/arm64-v8a/libplist-2.0.a | grep /Users/ | wc -l  # expect 0
EOF

echo ""
echo "Deps installed to $out"
echo "Provenance: $PROVENANCE"

# Verify no local paths leaked into the archives.
echo ""
echo "--- checking for leaked local paths ---"
CRYPTO_LEAKS="$(strings -a "$out/openssl/lib/arm64-v8a/libcrypto.a" 2>/dev/null | grep -c "/Users/" || true)"
PLIST_LEAKS="$(strings -a "$out/plist/lib/arm64-v8a/libplist-2.0.a" 2>/dev/null | grep -c "/Users/" || true)"
echo "libcrypto.a  /Users/ references: $CRYPTO_LEAKS  (expect: 0)"
echo "libplist-2.0.a /Users/ references: $PLIST_LEAKS  (expect: 0)"
if [ "$CRYPTO_LEAKS" -gt 0 ] || [ "$PLIST_LEAKS" -gt 0 ]; then
    echo "WARNING: local paths present in archives (build-host paths only, not keys)"
fi
