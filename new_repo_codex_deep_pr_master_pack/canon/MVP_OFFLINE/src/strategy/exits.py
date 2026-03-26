from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Tuple

from ..core.types import Position


def update_peak(pos: Position, price: float) -> None:
    if price > pos.peak_price:
        pos.peak_price = price


def maybe_partial_and_trail(pos: Position, price: float, cfg: Dict) -> None:
    if not pos.signal.mode.endswith("_aggr"):
        return

    base = pos.signal.mode.split("_")[0]
    m = cfg["modes"][base]
    gain = (price / pos.entry_price) - 1.0

    # partial take on trigger
    if (not pos.partial_taken) and gain >= float(m["aggr_trigger_gain"]):
        part = float(m["partial_take_pct"])
        qty = pos.remaining_usd * part
        pos.remaining_usd -= qty
        pos.realized_pnl_usd += qty * gain
        pos.partial_taken = True


def should_close(pos: Position, price: float, now: datetime, cfg: Dict) -> Tuple[bool, str]:
    base = pos.signal.mode.split("_")[0]
    m = cfg["modes"][base]
    gain = (price / pos.entry_price) - 1.0

    if gain >= float(pos.signal.tp_pct):
        return True, "TP"
    if gain <= float(pos.signal.sl_pct):
        return True, "SL"

    hold_max = int(m["hold_max"])
    if now >= pos.entry_ts + timedelta(seconds=hold_max):
        return True, "TIME"

    # trailing (only after partial in aggr)
    if pos.signal.mode.endswith("_aggr") and pos.partial_taken:
        trail = float(m["trail_from_peak_pct"])
        dd = (price / pos.peak_price) - 1.0
        if dd <= -trail:
            return True, "TRAIL"

    return False, ""
