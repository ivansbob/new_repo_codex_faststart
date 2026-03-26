"""integration/gates.py

P0.1 gate checks driven by strategy/config/params_base.yaml.

Goals:
- Deterministic & tiny (no external API calls).
- "No missing" for token gates: requires a local TokenSnapshot cache (or inline fields).
- Returns structured reject reasons so we can aggregate why signals were not emitted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .trade_types import Trade
from .token_snapshot_store import TokenSnapshot
from .reject_reasons import (
    MISSING_SNAPSHOT,
    MIN_LIQUIDITY_FAIL,
    MIN_VOLUME_24H_FAIL,
    MAX_SPREAD_FAIL,
    TOP10_HOLDERS_FAIL,
    SINGLE_HOLDER_FAIL,
    HONEYPOT_FAIL,
    WALLET_MIN_ROI_FAIL,
    WALLET_MIN_WINRATE_FAIL,
    WALLET_MIN_TRADES_FAIL,
)


@dataclass(frozen=True)
class GateDecision:
    passed: bool
    reasons: List[str]
    details: Dict[str, Any]

    @property
    def primary_reason(self) -> Optional[str]:
        return self.reasons[0] if self.reasons else None


def apply_gates(cfg: Dict[str, Any], trade: Trade, snapshot: Optional[TokenSnapshot]) -> GateDecision:
    reasons: List[str] = []
    details: Dict[str, Any] = {"mint": trade.mint, "tx_hash": trade.tx_hash}

    _token_gates(cfg=cfg, trade=trade, snapshot=snapshot, reasons=reasons, details=details)
    _honeypot_gate(cfg=cfg, trade=trade, reasons=reasons, details=details)
    _wallet_hard_filters(cfg=cfg, trade=trade, reasons=reasons, details=details)

    return GateDecision(passed=(len(reasons) == 0), reasons=reasons, details=details)


def _token_gates(cfg: Dict[str, Any], trade: Trade, snapshot: Optional[TokenSnapshot], reasons: List[str], details: Dict[str, Any]) -> None:
    gates = (((cfg.get("token_profile") or {}).get("gates")) or {})

    # Require snapshot for token gates (P0.1)
    if snapshot is None:
        reasons.append(MISSING_SNAPSHOT)
        details["missing_snapshot_for_mint"] = trade.mint
        return

    # Pull values (snapshot preferred; fallback to inline trade fields if present)
    liq = snapshot.liquidity_usd if snapshot.liquidity_usd is not None else trade.liquidity_usd
    vol24 = snapshot.volume_24h_usd if snapshot.volume_24h_usd is not None else trade.volume_24h_usd
    spread = snapshot.spread_bps if snapshot.spread_bps is not None else trade.spread_bps
    top10 = snapshot.top10_holders_pct if snapshot.top10_holders_pct is not None else None
    single = snapshot.single_holder_pct if snapshot.single_holder_pct is not None else None

    min_liq = gates.get("min_liquidity_usd")
    if min_liq is not None:
        if liq is None:
            reasons.append(MISSING_SNAPSHOT)
            details["missing_field"] = "liquidity_usd"
        elif float(liq) < float(min_liq):
            reasons.append(MIN_LIQUIDITY_FAIL)
            details["liquidity_usd"] = float(liq)
            details["min_liquidity_usd"] = float(min_liq)

    min_vol = gates.get("min_volume_24h_usd")
    if min_vol is not None:
        if vol24 is None:
            reasons.append(MISSING_SNAPSHOT)
            details["missing_field"] = "volume_24h_usd"
        elif float(vol24) < float(min_vol):
            reasons.append(MIN_VOLUME_24H_FAIL)
            details["volume_24h_usd"] = float(vol24)
            details["min_volume_24h_usd"] = float(min_vol)

    max_spread = gates.get("max_spread_bps")
    if max_spread is not None:
        if spread is None:
            reasons.append(MISSING_SNAPSHOT)
            details["missing_field"] = "spread_bps"
        elif float(spread) > float(max_spread):
            reasons.append(MAX_SPREAD_FAIL)
            details["spread_bps"] = float(spread)
            details["max_spread_bps"] = float(max_spread)

    max_top10 = gates.get("max_top10_holders_pct")
    if max_top10 is not None and top10 is not None:
        if float(top10) > float(max_top10):
            reasons.append(TOP10_HOLDERS_FAIL)
            details["top10_holders_pct"] = float(top10)
            details["max_top10_holders_pct"] = float(max_top10)

    max_single = gates.get("max_single_holder_pct")
    if max_single is not None and single is not None:
        if float(single) > float(max_single):
            reasons.append(SINGLE_HOLDER_FAIL)
            details["single_holder_pct"] = float(single)
            details["max_single_holder_pct"] = float(max_single)


def _honeypot_gate(cfg: Dict[str, Any], trade: Trade, reasons: List[str], details: Dict[str, Any]) -> None:
    token_profile = cfg.get("token_profile") or {}
    honeypot = token_profile.get("honeypot") or {}
    enabled = bool(honeypot.get("enabled"))
    if not enabled:
        return

    # P0.1: only boolean input; if missing or false -> fail when enabled.
    if trade.honeypot_pass is not True:
        reasons.append(HONEYPOT_FAIL)
        details["honeypot_pass"] = trade.honeypot_pass


def _wallet_hard_filters(cfg: Dict[str, Any], trade: Trade, reasons: List[str], details: Dict[str, Any]) -> None:
    hard = (((cfg.get("signals") or {}).get("hard_filters")) or {})

    min_wr = hard.get("min_wallet_winrate_30d")
    if min_wr is not None:
        if trade.wallet_winrate_30d is None:
            reasons.append(WALLET_MIN_WINRATE_FAIL)
            details["wallet_winrate_30d"] = None
            details["min_wallet_winrate_30d"] = float(min_wr)
        elif float(trade.wallet_winrate_30d) < float(min_wr):
            reasons.append(WALLET_MIN_WINRATE_FAIL)
            details["wallet_winrate_30d"] = float(trade.wallet_winrate_30d)
            details["min_wallet_winrate_30d"] = float(min_wr)

    min_roi = hard.get("min_wallet_roi_30d_pct")
    if min_roi is not None:
        if trade.wallet_roi_30d_pct is None:
            reasons.append(WALLET_MIN_ROI_FAIL)
            details["wallet_roi_30d_pct"] = None
            details["min_wallet_roi_30d_pct"] = float(min_roi)
        elif float(trade.wallet_roi_30d_pct) < float(min_roi):
            reasons.append(WALLET_MIN_ROI_FAIL)
            details["wallet_roi_30d_pct"] = float(trade.wallet_roi_30d_pct)
            details["min_wallet_roi_30d_pct"] = float(min_roi)

    min_tr = hard.get("min_wallet_trades_30d")
    if min_tr is not None:
        if trade.wallet_trades_30d is None:
            reasons.append(WALLET_MIN_TRADES_FAIL)
            details["wallet_trades_30d"] = None
            details["min_wallet_trades_30d"] = int(min_tr)
        elif int(trade.wallet_trades_30d) < int(min_tr):
            reasons.append(WALLET_MIN_TRADES_FAIL)
            details["wallet_trades_30d"] = int(trade.wallet_trades_30d)
            details["min_wallet_trades_30d"] = int(min_tr)
