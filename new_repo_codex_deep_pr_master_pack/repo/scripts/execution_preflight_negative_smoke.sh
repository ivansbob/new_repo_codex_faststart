#!/usr/bin/env bash
set -euo pipefail

# scripts/execution_preflight_negative_smoke.sh
#
# PR-6 negative smoke:
# - Exercise deterministic rejection branches for execution preflight
#   * ttl_sec=0 -> ttl_expired
#   * max_slippage_bps too low -> slippage_exceeded
#
# Success output (stderr, exactly):
#   [execution_preflight_negative] OK ✅

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

BASE_CFG="integration/fixtures/config/execution_preflight.yaml"
TRADES="integration/fixtures/trades.execution_preflight.jsonl"
SNAP="integration/fixtures/token_snapshot.sim_preflight.csv"
WPROF="integration/fixtures/wallet_profiles.sim_preflight.csv"
ALLOW="strategy/wallet_allowlist.yaml"

fail() {
  echo "ERROR: execution_preflight_negative_failed: $*" >&2
  exit 1
}

[[ -f "${BASE_CFG}" ]] || fail "missing fixture: ${BASE_CFG}"
[[ -f "${TRADES}" ]] || fail "missing fixture: ${TRADES}"
[[ -f "${SNAP}" ]] || fail "missing fixture: ${SNAP}"
[[ -f "${WPROF}" ]] || fail "missing fixture: ${WPROF}"
[[ -f "${ALLOW}" ]] || fail "missing allowlist: ${ALLOW}"

make_cfg() {
  local ttl="$1"
  local max_slip="$2"
  local out_path="$3"
  python3 - "${BASE_CFG}" "${ttl}" "${max_slip}" "${out_path}" <<'PY'
import sys
import yaml

base_path = sys.argv[1]
ttl = int(sys.argv[2])
max_slip = int(sys.argv[3])
out_path = sys.argv[4]

with open(base_path, 'r', encoding='utf-8') as f:
    cfg = yaml.safe_load(f) or {}

cfg.setdefault('execution_preflight', {})
cfg['execution_preflight']['ttl_sec'] = ttl
cfg['execution_preflight']['max_slippage_bps'] = max_slip

with open(out_path, 'w', encoding='utf-8') as f:
    yaml.safe_dump(cfg, f, sort_keys=False)
PY
}

run_case() {
  local case_name="$1"
  local cfg_path="$2"
  local exp_ttl="$3"
  local exp_slip="$4"

  local STDOUT_TMP
  local STDERR_TMP
  STDOUT_TMP="$(mktemp)"
  STDERR_TMP="$(mktemp)"

  set +e
  python3 -m integration.paper_pipeline \
    --dry-run \
    --summary-json \
    --sim-preflight \
    --execution-preflight \
    --config "${cfg_path}" \
    --allowlist "${ALLOW}" \
    --token-snapshot "${SNAP}" \
    --wallet-profiles "${WPROF}" \
    --trades-jsonl "${TRADES}" \
    1>"${STDOUT_TMP}" 2>"${STDERR_TMP}"
  local RC=$?
  set -e

  if [[ ${RC} -ne 0 ]]; then
    echo "ERROR: execution_preflight_negative_failed: ${case_name}: paper_pipeline exit=${RC}" >&2
    cat "${STDERR_TMP}" >&2
    exit 1
  fi

  local LINES
  LINES="$(python3 - <<PY
p = "${STDOUT_TMP}"
lines = [x for x in open(p, 'r', encoding='utf-8').read().splitlines() if x.strip()]
print(len(lines))
PY
)"

  if [[ "${LINES}" != "1" ]]; then
    echo "ERROR: execution_preflight_negative_failed: ${case_name}: expected stdout=1 line, got ${LINES}" >&2
    echo "ERROR: execution_preflight_negative_failed: stdout follows" >&2
    cat "${STDOUT_TMP}" >&2
    echo "ERROR: execution_preflight_negative_failed: stderr follows" >&2
    cat "${STDERR_TMP}" >&2
    exit 1
  fi

  python3 - "${STDOUT_TMP}" "${case_name}" "${exp_ttl}" "${exp_slip}" <<'PY' 1>/dev/null
import json
import sys

p = sys.argv[1]
case_name = sys.argv[2]
exp_ttl = int(sys.argv[3])
exp_slip = int(sys.argv[4])

line = [x for x in open(p, 'r', encoding='utf-8').read().splitlines() if x.strip()][0]
try:
    j = json.loads(line)
except Exception:
    print(f"ERROR: execution_preflight_negative_failed: {case_name}: invalid JSON on stdout", file=sys.stderr)
    sys.exit(1)

em = j.get('execution_metrics')
if not isinstance(em, dict):
    print(f"ERROR: execution_preflight_negative_failed: {case_name}: missing/invalid key execution_metrics", file=sys.stderr)
    sys.exit(1)

if em.get('schema_version') != 'execution_metrics.v1':
    print(f"ERROR: execution_preflight_negative_failed: {case_name}: schema_version mismatch", file=sys.stderr)
    print(json.dumps(em, ensure_ascii=False, indent=2, sort_keys=True), file=sys.stderr)
    sys.exit(1)

if int(em.get('filled', -1)) != 0:
    print(f"ERROR: execution_preflight_negative_failed: {case_name}: filled expected=0", file=sys.stderr)
    print(json.dumps(em, ensure_ascii=False, indent=2, sort_keys=True), file=sys.stderr)
    sys.exit(1)

rb = em.get('rejected_by_reason')
if not isinstance(rb, dict):
    print(f"ERROR: execution_preflight_negative_failed: {case_name}: rejected_by_reason missing/invalid", file=sys.stderr)
    print(json.dumps(em, ensure_ascii=False, indent=2, sort_keys=True), file=sys.stderr)
    sys.exit(1)

ttl = int(rb.get('ttl_expired', -1))
slp = int(rb.get('slippage_exceeded', -1))
if ttl != exp_ttl or slp != exp_slip:
    print(f"ERROR: execution_preflight_negative_failed: {case_name}: rejected_by_reason expected ttl_expired={exp_ttl} slippage_exceeded={exp_slip}", file=sys.stderr)
    print(json.dumps(em, ensure_ascii=False, indent=2, sort_keys=True), file=sys.stderr)
    sys.exit(1)
PY

  rm -f "${STDOUT_TMP}" "${STDERR_TMP}"
}

# Case 1: ttl_sec=0 => ttl_expired
CFG_TTL0="$(mktemp)"
make_cfg 0 50 "${CFG_TTL0}"
run_case "ttl0" "${CFG_TTL0}" 2 0
rm -f "${CFG_TTL0}"

# Case 2: max_slippage_bps too low => slippage_exceeded
CFG_SLIP="$(mktemp)"
make_cfg 10 1 "${CFG_SLIP}"
run_case "slippage_exceeded" "${CFG_SLIP}" 0 2
rm -f "${CFG_SLIP}"

# Success token (must be the final line emitted by this script)
echo "[execution_preflight_negative] OK ✅" >&2
