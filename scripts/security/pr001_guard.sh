#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

fail() {
  echo "[FAIL] $1" >&2
  exit 1
}

echo "[INFO] PR-001 security guard started"

# 1) Block dangerous private key material in committed files.
if rg -n --hidden --glob '!.git' --glob '!*.md' --glob '!*.txt' \
  'BEGIN (RSA|EC|OPENSSH|DSA) PRIVATE KEY' . >/tmp/pr001_keys.txt; then
  cat /tmp/pr001_keys.txt
  fail "Private key material detected"
fi

# 2) Block obvious high-risk credential variable assignments.
if rg -n --hidden --glob '!.git' \
  "(api[_-]?key|secret|token|password)\\s*[:=]\\s*['\"][^'\"]{8,}['\"]" . >/tmp/pr001_creds.txt; then
  cat /tmp/pr001_creds.txt
  fail "Potential hardcoded credentials detected"
fi

# 3) Reject oversized files (>5 MiB) at bootstrap stage.
LARGE_FILES=$(find . -type f -not -path './.git/*' -size +5M -print)
if [[ -n "$LARGE_FILES" ]]; then
  echo "$LARGE_FILES"
  fail "Oversized files detected (>5 MiB)"
fi

# 4) Require documentation artifacts for handoff continuity.
for required in HANDOFF_INTAKE.md PR_BOOTSTRAP_CHECKLIST.md; do
  [[ -f "$required" ]] || fail "Missing required doc: $required"
done

echo "[PASS] PR-001 security guard finished successfully"
