#!/bin/bash
# Host-native production core-protocol harness.
#
# Unity-builds the real raop.c + raop_handlers.h + http_handlers.h (via raop.c),
# the real http_request/http_response/rsakey/dnssd/dnssd_mdnsd, llhttp, and the
# host libplist + libcrypto. All networking (httpd, mdnsd sockets) is stubbed by
# tests/native/core_protocol_test.c, so the harness never opens a socket and
# never advertises on the LAN (mdnsd_start/announce/set_services are no-ops).
#
# Requires on the host: existing libplist-2.0 and OpenSSL 3 development files
# at an explicit prefix. This script never invokes a package manager (no brew);
# it only reads what is already installed. Override with PLIST_PREFIX /
# OPENSSL_PREFIX; defaults are the known pre-existing /opt/homebrew/opt paths.
# Actual host dependency versions are recorded in
# evidence/build/core-protocol-test.host-deps (nothing is installed).
# Evidence: evidence/build/core-protocol-test.{compile.log,argv,stdout,stderr,meta,host-deps}
set -uo pipefail

PROJ="$(cd "$(dirname "$0")/.." && pwd)"
ux="$PROJ/app/src/main/cpp/uxplay/lib"
test_src="$PROJ/tests/native/core_protocol_test.c"
mkdir -p "$PROJ/evidence/build"
evid="${PAD_EVIDENCE_DIR:-$(mktemp -d "$PROJ/evidence/build/core-protocol-run.XXXXXX")}"
mkdir -p "$evid"

PLIST_PREFIX="${PLIST_PREFIX:-/opt/homebrew/opt/libplist}"
OPENSSL_PREFIX="${OPENSSL_PREFIX:-/opt/homebrew/opt/openssl@3}"

for hdr in "$PLIST_PREFIX/include/plist/plist.h" "$OPENSSL_PREFIX/include/openssl/evp.h"; do
    if [ ! -f "$hdr" ]; then
        echo "ERROR: host dependency missing: $hdr" >&2
        echo "  set PLIST_PREFIX and OPENSSL_PREFIX to existing prefixes; this script installs nothing" >&2
        exit 2
    fi
done

# Record actual host dependency versions (read-only; nothing installed).
plist_ver="$(sed -n 's/^Version: *//p' "$PLIST_PREFIX/lib/pkgconfig/libplist-2.0.pc" 2>/dev/null | head -1)"
ssl_ver="$(sed -n 's/^# *define OPENSSL_VERSION_STR *"\([^"]*\)".*/\1/p' \
    "$OPENSSL_PREFIX/include/openssl/opensslv.h" 2>/dev/null | head -1)"
{
    echo "PLIST_PREFIX=$PLIST_PREFIX"
    echo "libplist-2.0 version=${plist_ver:-unknown}"
    echo "OPENSSL_PREFIX=$OPENSSL_PREFIX"
    echo "openssl version=${ssl_ver:-unknown}"
    echo "cc=$(${CC:-clang} --version 2>/dev/null | head -1)"
} > "$evid/core-protocol-test.host-deps"

CC="${CC:-clang}"
SAN="${SANITIZERS:-address,undefined}"
BIN="$(mktemp -d "${TMPDIR:-/tmp}/pad-core.XXXXXX")/core-protocol-test"
trap 'rm -rf "$(dirname "$BIN")"' EXIT

# --- compile (argv + compiler diagnostics recorded) ---
compile_cmd=("$CC" -g -O1 -fsanitize="$SAN" -fno-omit-frame-pointer -fno-sanitize-recover=all
    -DPLIST_230 -DTARGET_POSIX -D_XOPEN_SOURCE=700 -D_DARWIN_C_SOURCE
    -I"$ux" -I"$PLIST_PREFIX/include" -I"$OPENSSL_PREFIX/include"
    "$test_src"
    "$ux/llhttp/llhttp.c" "$ux/llhttp/api.c" "$ux/llhttp/http.c"
    "$ux/byteutils.c" "$ux/netutils.c" "$ux/logger.c" "$ux/utils.c" "$ux/compat.c"
    "$ux/crypto.c" "$ux/srp.c" "$ux/pairing.c"
    -L"$PLIST_PREFIX/lib" -L"$OPENSSL_PREFIX/lib"
    -lplist-2.0 -lcrypto -lpthread
    -o "$BIN")

{
    printf '%s\n' "${compile_cmd[@]}"
    echo "--- compiler output ---"
} > "$evid/core-protocol-test.compile.log"
"${compile_cmd[@]}" >> "$evid/core-protocol-test.compile.log" 2>&1
cc_status=$?
if [ $cc_status -ne 0 ]; then
    echo "COMPILE FAILED (exit $cc_status); see evidence/build/core-protocol-test.compile.log" >&2
    exit $cc_status
fi

# --- run (argv/stdout/stderr/exit recorded; failure path still records exit) ---
START="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf '%s\n' "$BIN" > "$evid/core-protocol-test.argv"
"$BIN" > "$evid/core-protocol-test.stdout" 2> "$evid/core-protocol-test.stderr"
run_status=$?
END="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
cat > "$evid/core-protocol-test.meta" << META
label: core-protocol-test
start: $START
end: $END
exit: $run_status
argv: $BIN
sanitizers: $SAN
META

echo "core-protocol-test exit: $run_status"
echo "evidence: $evid/core-protocol-test.{argv,stdout,stderr,meta}"
cat "$evid/core-protocol-test.stdout"
if [ -s "$evid/core-protocol-test.stderr" ]; then
    echo "--- stderr ---"
    cat "$evid/core-protocol-test.stderr"
fi
exit $run_status
