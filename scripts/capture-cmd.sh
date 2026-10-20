#!/bin/bash
# Usage: capture-cmd.sh <label> <logdir> cmd [args...]
# Captures: argv, exit, stdout, stderr, timing → <logdir>/<label>.*
set -euo pipefail
LABEL="$1"; DIR="$2"; shift 2
mkdir -p "$DIR"
START=$(date -u +%Y-%m-%dT%H:%M:%SZ)
printf '%s\n' "$@" > "$DIR/$LABEL.argv"
"$@" > "$DIR/$LABEL.stdout" 2> "$DIR/$LABEL.stderr"
EXIT=$?
END=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat > "$DIR/$LABEL.meta" << META
label: $LABEL
start: $START
end: $END
exit: $EXIT
argv: $(cat "$DIR/$LABEL.argv" | tr '\n' ' ')
META
echo "$EXIT"
