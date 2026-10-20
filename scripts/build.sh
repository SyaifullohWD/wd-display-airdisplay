#!/bin/bash
# Host-gated coherent delivery. Never claims device acceptance or calls adb.
set -euo pipefail
PROJ="$(cd "$(dirname "$0")/.." && pwd)"
export JAVA_HOME="${JAVA_HOME:-/Applications/Android Studio.app/Contents/jbr/Contents/Home}"
export ANDROID_HOME="${ANDROID_HOME:-$PROJ/.tools/sdk}"
if [ -d "$PROJ/.tools/ndk-r27d" ]; then
    export ANDROID_NDK_HOME="$PROJ/.tools/ndk-r27d"
fi
mkdir -p "$PROJ/evidence/fix-delivery"
LOG="$(mktemp "$PROJ/evidence/fix-delivery/delivery-run.XXXXXX")"
python3 -B "$PROJ/scripts/delivery.py" "$@" 2>&1 | tee "$LOG"
