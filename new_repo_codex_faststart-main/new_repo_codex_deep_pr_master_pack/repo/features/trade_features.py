"""features/trade_features.py

P0 feature builder (model-off friendly).

Contract:
- build_features(...) returns a JSON-serializable dict.
- Keys should be stable ("feature contract").
- Values should be floats/ints/bools/None.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from integration.trade_types import Trade
from integration.token_snapshot_store import TokenSnapshot
from integration.wallet_profile_store import WalletProfile


def build_features(
    trade: Trade,
    snapshot: Optional[TokenSnapshot],
    wallet_profile: Optional[WalletProfile],
) -> Dict[str, Any]:
    f: Dict[str, Any] = {
        "price_usd": trade.price,
        "size_usd": trade.size_usd,
        "is_buy": 1 if trade.side == "BUY" else 0,
    }

    if snapshot is not None:
        f.update(
            {
                "liquidity_usd": snapshot.liquidity_usd,
                "volume_24h_usd": snapshot.volume_24h_usd,
                "spread_bps": snapshot.spread_bps,
            }
        )
    else:
        f.update({"liquidity_usd": None, "volume_24h_usd": None, "spread_bps": None})

    f.update(
        {
            "wallet_roi_30d_pct": (wallet_profile.roi_30d_pct if wallet_profile else trade.wallet_roi_30d_pct),
            "wallet_winrate_30d": (wallet_profile.winrate_30d if wallet_profile else trade.wallet_winrate_30d),
            "wallet_trades_30d": (wallet_profile.trades_30d if wallet_profile else trade.wallet_trades_30d),
        }
    )

    return f


# -----------------------------
# miniML feature contract v1
# -----------------------------

# This contract is used by `tools/export_training_dataset.py` and enforced by
# `scripts/features_smoke.sh`. Keep keys stable.
FEATURE_KEYS_V1 = [
    "f_trade_size_usd",
    "f_price",
    "f_side_is_buy",
    "f_token_liquidity_usd",
    "f_token_spread_bps",
    "f_wallet_roi_30d_pct",
    "f_wallet_winrate_30d",
    "f_wallet_trades_30d",
]


def build_features_v1(
    trade: Trade,
    snapshot: Optional[TokenSnapshot],
    wallet_profile: Optional[WalletProfile],
) -> Dict[str, float]:
    """Return a stable set of numeric features for training/analysis.

    Requirements:
    - Always returns all FEATURE_KEYS_V1.
    - Missing data is encoded as 0.0.
    """

    def _f(x: Any) -> float:
        try:
            if x is None:
                return 0.0
            if isinstance(x, bool):
                return 1.0 if x else 0.0
            return float(x)
        except Exception:
            return 0.0

    side = str(getattr(trade, "side", "")).upper()
    out: Dict[str, float] = {
        "f_trade_size_usd": _f(getattr(trade, "size_usd", 0.0)),
        "f_price": _f(getattr(trade, "price", 0.0)),
        "f_side_is_buy": 1.0 if side == "BUY" else 0.0,
        "f_token_liquidity_usd": _f(getattr(snapshot, "liquidity_usd", 0.0) if snapshot else 0.0),
        "f_token_spread_bps": _f(getattr(snapshot, "spread_bps", 0.0) if snapshot else 0.0),
        "f_wallet_roi_30d_pct": _f(
            getattr(wallet_profile, "roi_30d_pct", None)
            if wallet_profile
            else getattr(trade, "wallet_roi_30d_pct", 0.0)
        ),
        "f_wallet_winrate_30d": _f(
            getattr(wallet_profile, "winrate_30d", None)
            if wallet_profile
            else getattr(trade, "wallet_winrate_30d", 0.0)
        ),
        "f_wallet_trades_30d": _f(
            getattr(wallet_profile, "trades_30d", None)
            if wallet_profile
            else getattr(trade, "wallet_trades_30d", 0.0)
        ),
    }

    # Defensive: ensure all keys exist.
    for k in FEATURE_KEYS_V1:
        out.setdefault(k, 0.0)
    return out
