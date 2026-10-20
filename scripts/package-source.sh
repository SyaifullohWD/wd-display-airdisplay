#!/bin/bash
# Compatibility entrypoint. Never pair a newly bundled source with a stale APK.
# A source-only update is intentionally no longer a publication operation:
# rerun host gates + build, then switch the complete delivery together.
set -euo pipefail
PROJ="$(cd "$(dirname "$0")/.." && pwd)"
exec bash "$PROJ/scripts/build.sh" "$@"
