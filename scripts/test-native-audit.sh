#!/bin/bash
# Actual decryptor and fragmented parser regressions; no LAN/device access.
# Production-linked regressions required before APK publication.
set -euo pipefail
PROJ="$(cd "$(dirname "$0")/.." && pwd)"
ux="$PROJ/app/src/main/cpp/uxplay/lib"
OPENSSL_PREFIX="${OPENSSL_PREFIX:-/opt/homebrew/opt/openssl@3}"
PLIST_PREFIX="${PLIST_PREFIX:-/opt/homebrew/opt/libplist}"
test -f "$OPENSSL_PREFIX/include/openssl/evp.h"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/pad-native-audit.XXXXXX")"
trap 'rm -rf "$WORK"' EXIT
mkdir -p "$PROJ/evidence/build"
EVIDENCE="${PAD_EVIDENCE_DIR:-$(mktemp -d "$PROJ/evidence/build/native-audit-run.XXXXXX")}"
mkdir -p "$EVIDENCE"
exec > >(tee "$EVIDENCE/native-audit.log") 2>&1
CC="${CC:-clang}"
flags=(-g -O1 "-fsanitize=${SANITIZERS:-address,undefined}" -fno-omit-frame-pointer
       -fno-sanitize-recover=all -DTARGET_POSIX -D_XOPEN_SOURCE=700 -D_DARWIN_C_SOURCE
       -DPLIST_230 -include signal.h -I"$ux" -I"$OPENSSL_PREFIX/include"
       -I"$PROJ/app/src/main/cpp/deps/plist/include")
set -x
"$CC" "${flags[@]}" "$PROJ/tests/native/crypto_stream_test.c" \
    "$ux/mirror_buffer.c" "$ux/crypto.c" "$ux/utils.c" \
    -L"$OPENSSL_PREFIX/lib" -lcrypto -o "$WORK/crypto-stream"
"$WORK/crypto-stream"
"$CC" "${flags[@]}" "$PROJ/tests/native/request_fragment_test.c" \
    "$ux/http_request.c" "$ux/llhttp/llhttp.c" "$ux/llhttp/api.c" "$ux/llhttp/http.c" \
    -o "$WORK/request-fragment"
"$WORK/request-fragment"
"$CC" "${flags[@]}" "$PROJ/tests/native/httpd_shutdown_test.c" \
    "$ux/http_request.c" "$ux/http_response.c" "$ux/netutils.c" "$ux/utils.c" "$ux/logger.c" \
    "$ux/llhttp/llhttp.c" "$ux/llhttp/api.c" "$ux/llhttp/http.c" \
    -lpthread -o "$WORK/httpd-shutdown"
for mode in 0 1 2 3 4 5 6 7 deadline valid backpressure; do
    "$WORK/httpd-shutdown" "$mode"
done
"$CC" "${flags[@]}" -DHTTPD_TEST_PRODUCTION_BUDGET "$PROJ/tests/native/httpd_shutdown_test.c" \
    "$ux/http_request.c" "$ux/http_response.c" "$ux/netutils.c" "$ux/utils.c" "$ux/logger.c" \
    "$ux/llhttp/llhttp.c" "$ux/llhttp/api.c" "$ux/llhttp/http.c" \
    -lpthread -o "$WORK/httpd-default-budget"
"$WORK/httpd-default-budget" deadline
"$CC" "${flags[@]}" "$PROJ/tests/native/dns_boundary_test.c" "$ux/utils.c" \
    -lpthread -o "$WORK/dns-boundaries"
"$WORK/dns-boundaries"
"$WORK/dns-boundaries" invalid-start
"$CC" "${flags[@]}" -I"$PROJ/app/src/main/cpp" \
    "$PROJ/tests/native/service_name_utf8_test.c" -o "$WORK/service-name-utf8"
"$WORK/service-name-utf8"
"$CC" "${flags[@]}" "$PROJ/tests/native/active_rekey_test.c" \
    "$ux/mirror_buffer.c" "$ux/crypto.c" "$ux/utils.c" "$ux/compat.c" \
    "$ux/byteutils.c" "$ux/netutils.c" "$ux/logger.c" \
    -L"$OPENSSL_PREFIX/lib" -lcrypto -L"$PLIST_PREFIX/lib" -lplist-2.0 -lpthread -o "$WORK/active-rekey"
"$WORK/active-rekey"
# Legacy TXT constants/synthetic policy checks supplement, not replace, the
# production-core handler suite enforced separately by host-gate.sh.
"$CC" "${flags[@]}" "$PROJ/tests/native/protocol_tests.c" -o "$WORK/protocol-constants"
"$WORK/protocol-constants"
