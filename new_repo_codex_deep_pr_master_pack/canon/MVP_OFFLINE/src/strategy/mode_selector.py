from __future__ import annotations

from typing import Dict

from ..core.types import WalletProfile


def base_mode_by_hold(wp: WalletProfile) -> str:
    h = wp.median_hold_sec
    if h < 40:
        return "U"
    if h < 100:
        return "S"
    if h < 220:
        return "M"
    return "L"


def choose_mode(wp: WalletProfile, price_change: float, dt_sec: int, cfg: Dict) -> str:
    base = base_mode_by_hold(wp)
    m = cfg["modes"][base]

    aggr = cfg.get("aggressive", {})
    if (
        aggr.get("enabled", False)
        and wp.tier in set(aggr.get("allowed_tiers", []))
        and price_change >= float(m.get("aggr_trigger_gain", 10**9))
        and dt_sec <= int(m.get("aggr_trigger_within", -1))
    ):
        return f"{base}_aggr"

    return f"{base}_base"
