from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

import yaml


def _pct_to_ratio(x: Any) -> float:
    try:
        return float(x) / 100.0
    except Exception:
        return 0.0


def _tier_allowed(min_tier: str) -> list[str]:
    # higher = stricter
    order = ["tier0", "tier1", "tier2", "tier3"]
    if min_tier not in order:
        return ["tier0", "tier1", "tier2"]
    idx = order.index(min_tier)
    return order[: idx + 1]


def normalize_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize rich v3.0 config into compact sections used by MVP_OFFLINE.

    MVP_OFFLINE modules historically expect:
      - wallet_gates
      - token_gates
      - modes (U/S/M/L base mode params + aggr triggers)
      - aggressive (global aggr gates)
      - risk
      - execution
      - defaults

    If a config already has these sections, we keep them as-is.
    If it has v3.0-style sections (wallet_profile/token_profile/signals), we derive the compact sections.
    """

    if not isinstance(cfg, dict):
        return {}

    # If already compact, nothing to do.
    if all(k in cfg for k in ("wallet_gates", "token_gates", "modes", "risk", "execution")):
        cfg.setdefault("defaults", {})
        return cfg

    # Detect v3 schema
    is_v3 = any(k in cfg for k in ("wallet_profile", "token_profile", "signals"))
    if not is_v3:
        cfg.setdefault("defaults", {})
        return cfg

    out = dict(cfg)

    # defaults
    out.setdefault("defaults", {})
    out["defaults"].setdefault("bankroll_usd", 10000)
    out["defaults"].setdefault("max_events", 100000)

    # Backward-compatible defaults for MVP_OFFLINE skeleton (used when input lacks profiles/snapshots)
    out["defaults"].setdefault("wallet_roi_30d", _pct_to_ratio((out.get("wallet_profile") or {}).get("filters", {}).get("min_roi_30d_pct", 20.0)))
    out["defaults"].setdefault("wallet_winrate", float((out.get("wallet_profile") or {}).get("filters", {}).get("min_winrate_30d", 0.60)))
    out["defaults"].setdefault("wallet_trades_30d", int((out.get("wallet_profile") or {}).get("filters", {}).get("min_trades_30d", 50)))
    out["defaults"].setdefault("wallet_median_hold_sec", 75)
    out["defaults"].setdefault("wallet_tier", "tier1")
    out["defaults"].setdefault("token_liquidity_usd", float((out.get("token_profile") or {}).get("gates", {}).get("min_liquidity_usd", 15000)))
    out["defaults"].setdefault("token_spread_bps", float((out.get("token_profile") or {}).get("gates", {}).get("max_spread_bps", 200)))

    # wallet_gates
    wf = (out.get("wallet_profile") or {}).get("filters") or {}
    out.setdefault(
        "wallet_gates",
        {
            "lookback_days": int(wf.get("lookback_days", 30)),
            "min_trades_30d": int(wf.get("min_trades_30d", 0)),
            "min_winrate": float(wf.get("min_winrate_30d", 0.0)),
            "min_roi_30d": _pct_to_ratio(wf.get("min_roi_30d_pct", 0.0)),
        },
    )

    # token_gates
    tg = (out.get("token_profile") or {}).get("gates") or {}
    hp = (out.get("token_profile") or {}).get("honeypot") or {}
    out.setdefault(
        "token_gates",
        {
            "min_liquidity_usd": float(tg.get("min_liquidity_usd", 0.0)),
            "min_volume_24h_usd": float(tg.get("min_volume_24h_usd", 0.0)),
            "max_spread_bps": float(tg.get("max_spread_bps", 10**9)),
            "max_top10_holders_pct": float(tg.get("max_top10_holders_pct", 100.0)),
            "max_single_holder_pct": float(tg.get("max_single_holder_pct", 100.0)),
            "honeypot": hp,
            "require_honeypot_pass": bool(hp.get("enabled", False)),
        },
    )

    # aggressive (global)
    aggr = ((out.get("signals") or {}).get("modes") or {}).get("aggressive") or {}
    sf = aggr.get("safety_filters") or {}
    out.setdefault(
        "aggressive",
        {
            "enabled": bool(aggr.get("enabled", False)),
            "allowed_tiers": _tier_allowed(str(sf.get("min_wallet_tier", "tier2"))),
            "min_wallet_winrate_30d": float(sf.get("min_wallet_winrate_30d", 0.0)),
            "min_wallet_roi_30d_pct": float(sf.get("min_wallet_roi_30d_pct", 0.0)),
            "min_liquidity_usd": float(sf.get("min_liquidity_usd", 0.0)),
            "max_spread_bps": float(sf.get("max_spread_bps", 10**9)),
        },
    )

    # modes (compact U/S/M/L)
    modes = {}
    sm = (out.get("signals") or {}).get("modes") or {}
    base_profiles: Mapping[str, Any] = sm.get("base_profiles") or {}
    triggers: Mapping[str, Any] = (sm.get("aggressive") or {}).get("triggers") or {}
    profiles: Mapping[str, Any] = (sm.get("aggressive") or {}).get("profiles") or {}

    for base in ("U", "S", "M", "L"):
        bp = base_profiles.get(base) or {}
        trig = triggers.get(base) or {}
        prof = profiles.get(f"{base}_aggr") or {}

        modes[base] = {
            "hold_max": int(bp.get("hold_sec_max", 60)),
            "ttl_sec": int(bp.get("ttl_sec", 60)),
            "tp_pct": _pct_to_ratio(bp.get("tp_pct", 0.0)),
            "sl_pct": _pct_to_ratio(bp.get("sl_pct", 0.0)),  # negative -> ok
            "aggr_trigger_gain": _pct_to_ratio(trig.get("require_price_change_pct", 10**9)),
            "aggr_trigger_within": int(trig.get("within_sec", -1)),
            "partial_take_pct": _pct_to_ratio(prof.get("partial_take_profit_pct_of_pos", 0.0)),
            "trail_from_peak_pct": _pct_to_ratio(prof.get("trailing_stop_pct_from_peak", 0.0)),
            "runner_tp_pct": _pct_to_ratio(prof.get("runner_tp_pct", 0.0)),
            "runner_sl_pct": _pct_to_ratio(prof.get("runner_sl_pct", 0.0)),
            "partial_tp_pct": _pct_to_ratio(prof.get("partial_tp_pct", 0.0)),
        }

    out.setdefault("modes", modes)

    # risk / execution passthrough (plus compact risk for MVP_OFFLINE)
    risk_v3 = out.get("risk") or {}
    out.setdefault("risk_v3", risk_v3)

    sizing = (risk_v3.get("sizing") or {}) if isinstance(risk_v3, dict) else {}
    limits = (risk_v3.get("limits") or {}) if isinstance(risk_v3, dict) else {}

    out["risk"] = {
        # MVP skeleton uses a fixed % sizing. In v3 config this lives in sizing.fixed_pct_of_bankroll (in %).
        "fixed_pos_pct": float(sizing.get("fixed_pct_of_bankroll", 1.0)) / 100.0,
        "max_open_positions": int(limits.get("max_open_positions", 20)),
        "max_daily_loss_pct": float(limits.get("max_daily_loss_pct", 7.0)) / 100.0,
        "max_exposure_per_token_pct": float(limits.get("max_exposure_per_token_pct", 10.0)) / 100.0,
    }

    out.setdefault("execution", out.get("execution") or {})
    # Compact execution defaults for MVP_OFFLINE simulator
    if isinstance(out.get("execution"), dict):
        sl = (out["execution"].get("slippage_model") or {})
        out["execution"].setdefault("entry_slippage_bps", float(sl.get("constant_bps", 80)))

    return out


def load_yaml(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    with p.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    return normalize_config(cfg)