#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

DOC_MODES="strategy/docs/overlay/PR_MODES_TUNING.md"
DOC_TIERS="strategy/docs/overlay/PR_WALLET_TIERS.md"
DOC_SIM="strategy/docs/overlay/PR_SIM_PREFLIGHT.md"
DOC_EXEC="strategy/docs/overlay/PR_EXECUTION_PREFLIGHT.md"

# --- PR_MODES_TUNING.md ---
if [[ ! -f "$DOC_MODES" ]]; then
  echo "ERROR: docs_smoke_missing: PR_MODES_TUNING.md" >&2
  exit 1
fi

grep -q "# PR-4A.5: Modes tuning playbook" "$DOC_MODES" || { echo "ERROR: docs_smoke_missing: heading_title" >&2; exit 1; }
grep -q "## Guardrails" "$DOC_MODES" || { echo "ERROR: docs_smoke_missing: heading_guardrails" >&2; exit 1; }
grep -q "## Results template" "$DOC_MODES" || { echo "ERROR: docs_smoke_missing: heading_results_template" >&2; exit 1; }
grep -q "\`__unknown_mode__\`" "$DOC_MODES" || { echo "ERROR: docs_smoke_missing: token___unknown_mode__" >&2; exit 1; }
grep -q "\`__no_mode__\`" "$DOC_MODES" || { echo "ERROR: docs_smoke_missing: token___no_mode__" >&2; exit 1; }

# --- PR_WALLET_TIERS.md ---
if [[ ! -f "$DOC_TIERS" ]]; then
  echo "ERROR: docs_smoke_missing: PR_WALLET_TIERS.md" >&2
  exit 1
fi

grep -q "PR-4B.1" "$DOC_TIERS" || { echo "ERROR: docs_smoke_missing: token_pr4b1" >&2; exit 1; }
grep -q "tier_counts" "$DOC_TIERS" || { echo "ERROR: docs_smoke_missing: token_tier_counts" >&2; exit 1; }
grep -q "\`__missing_wallet_profile__\`" "$DOC_TIERS" || { echo "ERROR: docs_smoke_missing: token___missing_wallet_profile__" >&2; exit 1; }
grep -q "Deterministic tiering rules" "$DOC_TIERS" || { echo "ERROR: docs_smoke_missing: token_deterministic_tiering_rules" >&2; exit 1; }

# --- PR_SIM_PREFLIGHT.md ---
if [[ ! -f "$DOC_SIM" ]]; then
  echo "ERROR: docs_smoke_missing: PR_SIM_PREFLIGHT.md" >&2
  exit 1
fi

grep -q "PR-5" "$DOC_SIM" || { echo "ERROR: docs_smoke_missing: token_pr5" >&2; exit 1; }
grep -q "sim_metrics.v1" "$DOC_SIM" || { echo "ERROR: docs_smoke_missing: token_sim_metrics_v1" >&2; exit 1; }
grep -q "ev_below_threshold" "$DOC_SIM" || { echo "ERROR: docs_smoke_missing: token_ev_below_threshold" >&2; exit 1; }
grep -q "Deterministic preflight" "$DOC_SIM" || { echo "ERROR: docs_smoke_missing: token_deterministic_preflight" >&2; exit 1; }

# --- PR_EXECUTION_PREFLIGHT.md ---
if [[ ! -f "$DOC_EXEC" ]]; then
  echo "ERROR: docs_smoke_missing: PR_EXECUTION_PREFLIGHT.md" >&2
  exit 1
fi

grep -q "PR-6" "$DOC_EXEC" || { echo "ERROR: docs_smoke_missing: token_pr6" >&2; exit 1; }
grep -q "execution_metrics.v1" "$DOC_EXEC" || { echo "ERROR: docs_smoke_missing: token_execution_metrics_v1" >&2; exit 1; }
grep -q "ttl_expired" "$DOC_EXEC" || { echo "ERROR: docs_smoke_missing: token_ttl_expired" >&2; exit 1; }
grep -q "Deterministic execution preflight" "$DOC_EXEC" || { echo "ERROR: docs_smoke_missing: token_deterministic_execution_preflight" >&2; exit 1; }


DOC_RESULTS="strategy/docs/overlay/RESULTS_TEMPLATE.md"
JSON_RESULTS="strategy/docs/overlay/results/results_v1.json"

# --- RESULTS_TEMPLATE.md ---
if [[ ! -f "$DOC_RESULTS" ]]; then
  echo "ERROR: docs_smoke_missing: RESULTS_TEMPLATE.md" >&2
  exit 1
fi

grep -q "RESULTS_TEMPLATE.v1" "$DOC_RESULTS" || { echo "ERROR: docs_smoke_missing: token_RESULTS_TEMPLATE_v1" >&2; exit 1; }
grep -q "Modes summary" "$DOC_RESULTS" || { echo "ERROR: docs_smoke_missing: token_modes_summary" >&2; exit 1; }
grep -q "Wallet tiers summary" "$DOC_RESULTS" || { echo "ERROR: docs_smoke_missing: token_wallet_tiers_summary" >&2; exit 1; }
grep -q "Decision log" "$DOC_RESULTS" || { echo "ERROR: docs_smoke_missing: token_decision_log" >&2; exit 1; }
grep -q "Next parameter changes" "$DOC_RESULTS" || { echo "ERROR: docs_smoke_missing: token_next_parameter_changes" >&2; exit 1; }

# --- results_v1.json (must be valid JSON) ---
if [[ ! -f "$JSON_RESULTS" ]]; then
  echo "ERROR: docs_smoke_missing: results_v1.json" >&2
  exit 1
fi
python3 - <<'PY_JSON' "$JSON_RESULTS"
import json, sys
p = sys.argv[1]
try:
    with open(p, "r", encoding="utf-8") as f:
        json.load(f)
except Exception as e:
    print(f"ERROR: docs_smoke_missing: results_v1_json_invalid", file=sys.stderr)
    raise SystemExit(1)
PY_JSON
echo "[docs_smoke] OK ✅" >&2
