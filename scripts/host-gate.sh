#!/bin/bash
# Host-only acceptance. This does not establish device or AirPlay interoperability.
set -euo pipefail
PROJ="$(cd "$(dirname "$0")/.." && pwd)"
cd "$PROJ"
mkdir -p "$PROJ/evidence/build"
export PAD_EVIDENCE_DIR="$(mktemp -d "$PROJ/evidence/build/host-gate-run.XXXXXX")"
export JAVA_HOME="${JAVA_HOME:-/Applications/Android Studio.app/Contents/jbr/Contents/Home}"
export ANDROID_HOME="${ANDROID_HOME:-$PROJ/.tools/sdk}"
export SANITIZERS="${SANITIZERS:-address,undefined}"
./gradlew :app:testDebugUnitTest --rerun-tasks
bash scripts/test-native.sh
bash scripts/test-core-protocol.sh
# Dedicated real-crypto and request-fragment regressions are mandatory.
bash scripts/test-native-audit.sh
for suite in test_apk_alignment.py test_delivery.py test_device_startup.py; do
    test -f "tests/$suite"
    echo "--- $suite ---"
    python3 -B -m unittest discover -s tests -p "$suite" -v
done
printf '%s\n' 'HOST GATE PASS (not device acceptance)'
