#!/usr/bin/env bash
set -euo pipefail

# scripts/execution_preflight_smoke.sh
#
# PR-6 positive smoke:
# - Run paper_pipeline with --summary-json --execution-preflight
# - Verify stdout: exactly one JSON line
# - Verify execution_metrics: schema_version + deterministic counters
#
# Success output (stderr, exactly):
#   [execution_preflight] OK ✅

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

CFG="integration/fixtures/config/execution_preflight.yaml"
TRADES="integration/fixtures/trades.execution_preflight.jsonl"
SNAP="integration/fixtures/token_snapshot.sim_preflight.csv"
WPROF="integration/fixtures/wallet_profiles.sim_preflight.csv"
ALLOW="strategy/wallet_allowlist.yaml"

fail() {
  echo "ERROR: execution_preflight_failed: $*" >&2
  exit 1
}

[[ -f "${CFG}" ]] || fail "missing fixture: ${CFG}"
[[ -f "${TRADES}" ]] || fail "missing fixture: ${TRADES}"
[[ -f "${SNAP}" ]] || fail "missing fixture: ${SNAP}"
[[ -f "${WPROF}" ]] || fail "missing fixture: ${WPROF}"
[[ -f "${ALLOW}" ]] || fail "missing allowlist: ${ALLOW}"

STDOUT_TMP="$(mktemp)"
STDERR_TMP="$(mktemp)"
cleanup() {
  rm -f "${STDOUT_TMP}" "${STDERR_TMP}"
}
trap cleanup EXIT

set +e
python3 -m integration.paper_pipeline \
  --dry-run \
  --summary-json \
  --sim-preflight \
  --execution-preflight \
  --config "${CFG}" \
  --allowlist "${ALLOW}" \
  --token-snapshot "${SNAP}" \
  --wallet-profiles "${WPROF}" \
  --trades-jsonl "${TRADES}" \
  1>"${STDOUT_TMP}" 2>"${STDERR_TMP}"
RC=$?
set -e

if [[ ${RC} -ne 0 ]]; then
  echo "ERROR: execution_preflight_failed: paper_pipeline exit=${RC}" >&2
  echo "ERROR: execution_preflight_failed: stderr follows" >&2
  cat "${STDERR_TMP}" >&2
  exit 1
fi

# Verify stdout has exactly 1 non-empty line
LINES="$(python3 - <<PY
p = "${STDOUT_TMP}"
lines = [x for x in open(p, "r", encoding="utf-8").read().splitlines() if x.strip()]
print(len(lines))
PY
)"

if [[ "${LINES}" != "1" ]]; then
  echo "ERROR: execution_preflight_failed: expected stdout=1 line, got ${LINES}" >&2
  echo "ERROR: execution_preflight_failed: stdout follows" >&2
  cat "${STDOUT_TMP}" >&2
  echo "ERROR: execution_preflight_failed: stderr follows" >&2
  cat "${STDERR_TMP}" >&2
  exit 1
fi

# Parse JSON + assert execution_metrics contract
python3 - "${STDOUT_TMP}" <<'PY' 1>/dev/null
import json
import sys

p = sys.argv[1]
line = [x for x in open(p, "r", encoding="utf-8").read().splitlines() if x.strip()][0]
try:
    j = json.loads(line)
except Exception:
    print("ERROR: execution_preflight_failed: invalid JSON on stdout", file=sys.stderr)
    sys.exit(1)

em = j.get("execution_metrics")
if not isinstance(em, dict):
    print("ERROR: execution_preflight_failed: missing/invalid key execution_metrics", file=sys.stderr)
    sys.exit(1)

if em.get("schema_version") != "execution_metrics.v1":
    print("ERROR: execution_preflight_failed: execution_metrics.schema_version mismatch", file=sys.stderr)
    print(json.dumps(em, ensure_ascii=False, indent=2, sort_keys=True), file=sys.stderr)
    sys.exit(1)

if int(em.get("attempted", -1)) != 2:
    print("ERROR: execution_preflight_failed: attempted expected=2", file=sys.stderr)
    print(json.dumps(em, ensure_ascii=False, indent=2, sort_keys=True), file=sys.stderr)
    sys.exit(1)

if int(em.get("filled", -1)) != 1:
    print("ERROR: execution_preflight_failed: filled expected=1", file=sys.stderr)
    print(json.dumps(em, ensure_ascii=False, indent=2, sort_keys=True), file=sys.stderr)
    sys.exit(1)

rb = em.get("rejected_by_reason")
if not isinstance(rb, dict):
    print("ERROR: execution_preflight_failed: rejected_by_reason missing/invalid", file=sys.stderr)
    print(json.dumps(em, ensure_ascii=False, indent=2, sort_keys=True), file=sys.stderr)
    sys.exit(1)

if int(rb.get("ttl_expired", -1)) != 1:
    print("ERROR: execution_preflight_failed: ttl_expired expected=1", file=sys.stderr)
    print(json.dumps(em, ensure_ascii=False, indent=2, sort_keys=True), file=sys.stderr)
    sys.exit(1)

# Optional sanity checks (diff-friendly)
if int(rb.get("slippage_exceeded", -1)) != 0:
    print("ERROR: execution_preflight_failed: slippage_exceeded expected=0", file=sys.stderr)
    print(json.dumps(em, ensure_ascii=False, indent=2, sort_keys=True), file=sys.stderr)
    sys.exit(1)

fill_rate = float(em.get("fill_rate", 0.0))
if abs(fill_rate - 0.5) > 1e-9:
    print("ERROR: execution_preflight_failed: fill_rate expected=0.5", file=sys.stderr)
    print(json.dumps(em, ensure_ascii=False, indent=2, sort_keys=True), file=sys.stderr)
    sys.exit(1)
PY

# Success token (must be the final line emitted by this script)
echo "[execution_preflight] OK ✅" >&2
