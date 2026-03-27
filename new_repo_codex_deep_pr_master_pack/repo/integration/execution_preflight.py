"""integration/execution_preflight.py

PR-6: deterministic offline "execution preflight" layer.

Purpose
- Compute a minimal `execution_metrics.v1` contract (fill / slippage / TTL)
  WITHOUT external APIs, randomness, or wall-clock time.

Model (MVP, deterministic)
- Consider BUY trades as entry attempts.
- A trade is FILLED iff:
    * ttl_sec > 0
    * token snapshot spread_bps <= max_slippage_bps
    * there exists at least one future tick for the same mint with
      entry_ts < tick_ts <= entry_ts + ttl_sec
- Rejections:
    * ttl_expired: ttl_sec <= 0 OR no future ticks in TTL window
    * slippage_exceeded: spread_bps > max_slippage_bps
- Slippage model (for filled trades):
    fill_price = entry_price * (1 + slippage_bps / 10_000)

This module performs no I/O.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Mapping, MutableMapping, Optional, Tuple


EXEC_SCHEMA_VERSION = "execution_metrics.v1"

REJECT_TTL_EXPIRED = "ttl_expired"
REJECT_SLIPPAGE_EXCEEDED = "slippage_exceeded"


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        return obj.get(key, default)
    if hasattr(obj, key):
        return getattr(obj, key)
    return default


def _ts_to_seconds(ts: Any) -> float:
    """Parse trade ts into seconds.

    Supported (deterministic):
    - numeric strings / numbers: treated as unix seconds
    - ISO-like strings: parsed as UTC (naive -> UTC)
    """
    if ts is None:
        return 0.0

    try:
        return float(ts)
    except Exception:
        pass

    s = str(ts).strip()
    if not s:
        return 0.0

    if s.endswith("Z"):
        s2 = s[:-1] + "+00:00"
    else:
        s2 = s

    try:
        dt = datetime.fromisoformat(s2)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.timestamp()
    except Exception:
        return 0.0


def _as_float(x: Any, default: float = 0.0) -> float:
    try:
        return float(x)
    except Exception:
        return default


def _as_int(x: Any, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return default


def execution_preflight_and_simulate(
    trades_norm: List[dict],
    token_snapshot: Dict[str, dict],
    cfg: dict,
) -> dict:
    """Compute deterministic execution metrics.

    Args:
      trades_norm: normalized trades (dicts). Must include entries and future ticks.
      token_snapshot: mapping mint -> snapshot dict (must include spread_bps when available).
      cfg: strategy config dict (expects cfg["execution_preflight"] subtree).

    Returns:
      execution_metrics dict (schema_version="execution_metrics.v1").
    """

    exec_cfg = (cfg.get("execution_preflight") or {}) if isinstance(cfg, dict) else {}

    ttl_sec = _as_int(exec_cfg.get("ttl_sec", 0), 0)
    max_slippage_bps = _as_int(exec_cfg.get("max_slippage_bps", 0), 0)
    slippage_bps = _as_float(exec_cfg.get("slippage_bps", 0.0), 0.0)

    # Index all ticks by mint: list of (ts_sec, price)
    ticks_by_mint: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
    for t in trades_norm:
        mint = str(_get(t, "mint", "") or "")
        if not mint:
            continue
        ts_sec = _ts_to_seconds(_get(t, "ts", ""))
        price = _as_float(_get(t, "price", None), default=None)  # type: ignore[arg-type]
        if price is None:
            continue
        ticks_by_mint[mint].append((ts_sec, float(price)))

    for mint, arr in ticks_by_mint.items():
        arr.sort(key=lambda x: x[0])

    attempted = 0
    filled = 0
    rejected_by_reason: MutableMapping[str, int] = {
        REJECT_TTL_EXPIRED: 0,
        REJECT_SLIPPAGE_EXCEEDED: 0,
    }

    slippage_sum = 0.0

    for t in trades_norm:
        side = str(_get(t, "side", "") or "").upper()
        if side != "BUY":
            continue

        attempted += 1

        mint = str(_get(t, "mint", "") or "")
        entry_ts = _ts_to_seconds(_get(t, "ts", ""))

        # 1) TTL must be positive
        if ttl_sec <= 0:
            rejected_by_reason[REJECT_TTL_EXPIRED] += 1
            continue

        # 2) Slippage gate (proxy via snapshot spread)
        snap = token_snapshot.get(mint) if isinstance(token_snapshot, dict) else None
        spread_bps = _as_float((snap or {}).get("spread_bps", None), default=10_000.0)
        if spread_bps > float(max_slippage_bps):
            rejected_by_reason[REJECT_SLIPPAGE_EXCEEDED] += 1
            continue

        # 3) TTL window must contain at least one future tick
        window_end = entry_ts + float(ttl_sec)
        ticks = ticks_by_mint.get(mint, [])
        saw_tick_in_window = False
        for ts_sec, _px in ticks:
            if ts_sec <= entry_ts:
                continue
            if ts_sec > window_end:
                break
            saw_tick_in_window = True
            break

        if not saw_tick_in_window:
            rejected_by_reason[REJECT_TTL_EXPIRED] += 1
            continue

        # Filled
        filled += 1
        slippage_sum += slippage_bps

        # Deterministic fill_price computation (kept for future extension; not returned in v1)
        # entry_price = _as_float(_get(t, "price", 0.0), 0.0)
        # _fill_price = entry_price * (1.0 + slippage_bps / 10_000.0)

    fill_rate = (float(filled) / float(attempted)) if attempted else 0.0
    avg_slippage_bps = int(round(slippage_sum / float(filled))) if filled else 0

    return {
        "schema_version": EXEC_SCHEMA_VERSION,
        "attempted": int(attempted),
        "filled": int(filled),
        "fill_rate": float(fill_rate),
        "avg_slippage_bps": int(avg_slippage_bps),
        "rejected_by_reason": {
            REJECT_TTL_EXPIRED: int(rejected_by_reason.get(REJECT_TTL_EXPIRED, 0)),
            REJECT_SLIPPAGE_EXCEEDED: int(rejected_by_reason.get(REJECT_SLIPPAGE_EXCEEDED, 0)),
        },
    }
