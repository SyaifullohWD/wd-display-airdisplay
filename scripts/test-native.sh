#!/bin/bash
set -euo pipefail
PROJ="$(cd "$(dirname "$0")/.." && pwd)"
ux="$PROJ/app/src/main/cpp/uxplay/lib"
test_dir="$(mktemp -d "${TMPDIR:-/tmp}/pad-native.XXXXXX")"
trap 'rm -rf "$test_dir"' EXIT
mkdir -p "$PROJ/evidence/build"
EVIDENCE="${PAD_EVIDENCE_DIR:-$(mktemp -d "$PROJ/evidence/build/native-run.XXXXXX")}"
mkdir -p "$EVIDENCE"
LOG="$EVIDENCE/native-tests.log"
echo "=== Pocket AirDisplay native host tests $(date -u +%Y-%m-%dT%H:%M:%SZ) ===" | tee "$LOG"

echo "--- mirror_regression ---" | tee -a "$LOG"
"${CC:-clang}" -g -O1 -fsanitize="${SANITIZERS:-undefined}" \
  -fno-omit-frame-pointer -fno-sanitize-recover=all \
  -DPLIST_230 -DTARGET_POSIX -D_XOPEN_SOURCE=700 -D_DARWIN_C_SOURCE \
  -include signal.h -I"$ux" -I"$PROJ/app/src/main/cpp/deps/plist/include" \
  "$PROJ/tests/native/mirror_regression.c" \
  "$ux/byteutils.c" "$ux/netutils.c" "$ux/logger.c" \
  -lpthread -o "$test_dir/mirror-regression" 2>&1 | tee -a "$LOG"
"$test_dir/mirror-regression" 2>&1 | tee -a "$LOG"
echo "mirror_regression exit: ${PIPESTATUS[0]}" | tee -a "$LOG"

echo "--- dmap_test ---" | tee -a "$LOG"
"${CC:-clang}" -g -O1 -fsanitize="${SANITIZERS:-undefined}" \
  -fno-omit-frame-pointer -fno-sanitize-recover=all \
  -I"$PROJ/app/src/main/cpp" \
  "$PROJ/tests/native/dmap_test.c" "$PROJ/app/src/main/cpp/dmap.c" \
  -o "$test_dir/dmap-test" 2>&1 | tee -a "$LOG"
"$test_dir/dmap-test" 2>&1 | tee -a "$LOG"
echo "dmap_test exit: ${PIPESTATUS[0]}" | tee -a "$LOG"

echo "=== DONE ===" | tee -a "$LOG"
