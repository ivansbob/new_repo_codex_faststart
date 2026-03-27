from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Dict, List

from ..core.types import Signal, Position, Trade
from ..strategy.exits import update_peak, maybe_partial_and_trail, should_close


@dataclass
class SimResult:
    positions: List[Position]
    total_pnl_usd: float


def simulate_fill_entry(signal: Signal, cfg: Dict) -> float:
    # MVP: fixed slippage on entry
    bps = float(cfg["execution"]["entry_slippage_bps"])
    return signal.trade.price * (1.0 + bps / 10_000.0)


def simulate_position(signal: Signal, future_ticks: List[Trade], cfg: Dict) -> Position:
    entry_price = simulate_fill_entry(signal, cfg)

    pos = Position(
        id=f"{signal.trade.tx_hash}:{signal.trade.wallet}",
        signal=signal,
        entry_ts=signal.trade.ts,
        entry_price=entry_price,
        size_usd=signal.size_usd,
        peak_price=entry_price,
        remaining_usd=signal.size_usd,
    )

    hold_end = signal.trade.ts + timedelta(seconds=int(cfg["modes"][signal.mode.split('_')[0]]["hold_max"]))

    for t in future_ticks:
        if t.ts <= signal.trade.ts:
            continue
        if t.ts > hold_end:
            break

        price = float(t.price)
        update_peak(pos, price)
        maybe_partial_and_trail(pos, price, cfg)
        close, reason = should_close(pos, price, t.ts, cfg)
        if close:
            pos.is_closed = True
            pos.exit_ts = t.ts
            pos.exit_price = price

            gain = (price / pos.entry_price) - 1.0
            pos.realized_pnl_usd += pos.remaining_usd * gain
            pos.remaining_usd = 0.0
            pos.exit_reason = reason
            return pos

    # if not closed within window -> close at hold_end (last known price)
    last_price = float(future_ticks[-1].price) if future_ticks else float(signal.trade.price)
    pos.is_closed = True
    pos.exit_ts = hold_end
    pos.exit_price = last_price
    gain = (last_price / pos.entry_price) - 1.0
    pos.realized_pnl_usd += pos.remaining_usd * gain
    pos.remaining_usd = 0.0
    pos.exit_reason = "TIME"
    return pos


def run_simulation(signals: List[Signal], trades: List[Trade], cfg: Dict) -> SimResult:
    by_token: Dict[str, List[Trade]] = {}
    for t in trades:
        by_token.setdefault(t.token_mint, []).append(t)
    for k in by_token:
        by_token[k].sort(key=lambda x: x.ts)

    positions: List[Position] = []
    total = 0.0
    for s in signals:
        future = by_token.get(s.trade.token_mint, [])
        pos = simulate_position(s, future, cfg)
        positions.append(pos)
        total += pos.realized_pnl_usd

    return SimResult(positions=positions, total_pnl_usd=total)
