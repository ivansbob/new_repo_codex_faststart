#!/usr/bin/env bash
set -euo pipefail

# scripts/overlay_lint.sh
#
# Purpose:
#   Guardrails so "strategy overlay" stays docs-only and CANON stays single-source-of-truth.
#   This script is safe to run locally or in CI.
#
# Rules enforced:
#   1) vendor/gmee_canon/** exists (CANON).
#   2) No "golden-engine-exit/**" directory anywhere OUTSIDE vendor/.
#   3) No *.sql / *.ddl files anywhere OUTSIDE vendor/.
#   4) Overlay docs must live under strategy/docs/overlay/** only.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail() {
  echo "overlay_lint: FAIL: $*" >&2
  exit 1
}

pass() {
  echo "overlay_lint: OK: $*"
}

# 1) CANON exists
if [[ ! -d "${ROOT_DIR}/vendor/gmee_canon" ]]; then
  fail "Missing vendor/gmee_canon (CANON)."
fi
pass "vendor/gmee_canon present"

# Helper: list matches excluding vendor/*
# Using 'find' with -print0 for safety.
find_outside_vendor() {
  local pattern="$1"
  (cd "${ROOT_DIR}" &&     find . -path './vendor/*' -prune -o -name "${pattern}" -print)
}

# 2) No golden-engine-exit outside vendor
golden_hits="$(cd "${ROOT_DIR}" && find . -path './vendor/*' -prune -o -type d -name 'golden-engine-exit' -print)"
if [[ -n "${golden_hits}" ]]; then
  echo "${golden_hits}" >&2
  fail "Found golden-engine-exit directory outside vendor/. Overlay must be docs-only."
fi
pass "no golden-engine-exit outside vendor"

# 3) No SQL/DDL outside vendor
sql_hits="$(cd "${ROOT_DIR}" && find . -path './vendor/*' -prune -o -type f \( -name '*.sql' -o -name '*.ddl' \) -print)"
if [[ -n "${sql_hits}" ]]; then
  echo "${sql_hits}" >&2
  fail "Found *.sql/*.ddl outside vendor/. SQL/DDL must live only in vendor/gmee_canon (CANON)."
fi
pass "no *.sql/*.ddl outside vendor"

# 4) Overlay docs only under strategy/docs/overlay
# If someone creates 'overlay' folder elsewhere under strategy/docs, that's fine only if it is exactly that path.
overlay_dirs="$(cd "${ROOT_DIR}" && find strategy -type d -name 'overlay' -print 2>/dev/null || true)"
for d in ${overlay_dirs}; do
  if [[ "${d}" != "strategy/docs/overlay" ]]; then
    echo "${d}" >&2
    fail "Unexpected overlay directory location: ${d}. Expected only strategy/docs/overlay."
  fi
done
pass "overlay directory location OK"

# 5) Overlay docs should not reference legacy paths that confuse agents.
# If you must reference something legacy for historical context, prefix the line with:
#   LEGACY_PATH: golden-engine-exit/...
legacy_refs="$(grep -R "golden-engine-exit" -n "${ROOT_DIR}/strategy/docs/overlay" 2>/dev/null || true)"
if [[ -n "${legacy_refs}" ]]; then
  bad_refs="$(echo "${legacy_refs}" | grep -v "LEGACY_PATH:" || true)"
  if [[ -n "${bad_refs}" ]]; then
    echo "${bad_refs}" >&2
    fail "Overlay references legacy path golden-engine-exit without LEGACY_PATH banner."
  fi
fi

pass "no confusing legacy paths in overlay"

echo "[overlay_lint] linting PR labels (SoT vs docs)" >&2

bash scripts/pr_labels_lint.sh

echo "[overlay_lint] running modes smoke" >&2
bash scripts/modes_smoke.sh

echo "[overlay_lint] running tiers smoke" >&2
bash scripts/tiers_smoke.sh

echo "[overlay_lint] running docs smoke" >&2


bash scripts/docs_smoke.sh

echo "[overlay_lint] running sim preflight smoke" >&2
bash scripts/sim_preflight_smoke.sh

echo "[overlay_lint] running sim preflight negative smoke" >&2
bash scripts/sim_preflight_negative_smoke.sh

echo "[overlay_lint] running execution preflight smoke" >&2
bash scripts/execution_preflight_smoke.sh

echo "[overlay_lint] running execution preflight negative smoke" >&2
bash scripts/execution_preflight_negative_smoke.sh

echo "overlay_lint: ALL CHECKS PASSED"
