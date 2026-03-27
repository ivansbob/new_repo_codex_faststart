"""integration/reject_reasons.py

Canonical reject reasons for Iteration-1 pipeline.

Keep as simple string constants so we can:
- aggregate stats (why did we NOT emit a signal?)
- avoid ad-hoc reason strings drifting across modules
"""

# Input / enrichment
MISSING_SNAPSHOT = "missing_snapshot"
INVALID_TRADE = "invalid_trade"

# Token gates
MIN_LIQUIDITY_FAIL = "min_liquidity_fail"
MIN_VOLUME_24H_FAIL = "min_volume_24h_fail"
MAX_SPREAD_FAIL = "max_spread_fail"
TOP10_HOLDERS_FAIL = "top10_holders_fail"
SINGLE_HOLDER_FAIL = "single_holder_fail"

# Honeypot / rug (P0.1: boolean only)
HONEYPOT_FAIL = "honeypot_fail"

# Wallet hard filters
WALLET_MIN_WINRATE_FAIL = "wallet_min_winrate_fail"
WALLET_MIN_ROI_FAIL = "wallet_min_roi_fail"
WALLET_MIN_TRADES_FAIL = "wallet_min_trades_fail"

# Risk (stubbed in P0.1)
RISK_LIMIT_FAIL = "risk_limit_fail"

# -----------------------------
# Guardrail: enum-only reasons
# -----------------------------

# Collect all uppercase string constants defined in this module.
_KNOWN_REASONS = {
    v for k, v in globals().items() if k.isupper() and isinstance(v, str)
}


def assert_reason_known(reason: str) -> None:
    """Raise if the provided reason isn't in the canonical set.

    This is intentionally strict so any new reason requires:
    - updating this file
    - updating fixtures/expected_counts where applicable
    """

    if reason not in _KNOWN_REASONS:
        raise ValueError(f"Unknown reject_reason: {reason!r}. Add it to integration/reject_reasons.py")
