from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from ..core.types import Trade, WalletProfile, TokenState, Signal
from .mode_selector import choose_mode


def hard_gates(wp: WalletProfile, ts: TokenState, cfg: Dict) -> bool:
    wg = cfg["wallet_gates"]
    tg = cfg["token_gates"]

    if wp.trades_30d < int(wg["min_trades_30d"]):
        return False
    if wp.winrate < float(wg["min_winrate"]):
        return False
    if wp.roi_30d < float(wg["min_roi_30d"]):
        return False

    if ts.liquidity_usd < float(tg["min_liquidity_usd"]):
        return False
    if ts.spread_bps > float(tg["max_spread_bps"]):
        return False
    if bool(tg.get("require_honeypot_pass", False)) and ts.honeypot_flag:
        return False

    return True


def build_signal(
    trade: Trade,
    wp: WalletProfile,
    ts: TokenState,
    leader_entry_ts: datetime,
    cfg: Dict,
) -> Optional[Signal]:
    # MVP: only buys generate signals
    if trade.side != "buy":
        return None

    if not hard_gates(wp, ts, cfg):
        return None

    dt_sec = max(0, int((trade.ts - leader_entry_ts).total_seconds()))
    price_change = (ts.price / trade.price) - 1.0 if trade.price > 0 else 0.0

    mode = choose_mode(wp, price_change, dt_sec, cfg)
    base = mode.split("_")[0]
    m = cfg["modes"][base]

    # MVP: no ML/EV yet; gates imply “candidate edge”
    return Signal(
        trade=trade,
        wallet_profile=wp,
        token_state=ts,
        mode=mode,
        risk_regime=0.0,  # overlay placeholder in MVP_OFFLINE

        size_usd=0.0,  # filled by RiskEngine
        ttl_sec=int(m["ttl_sec"]),
        tp_pct=float(m["tp_pct"]),
        sl_pct=float(m["sl_pct"]),
    )
