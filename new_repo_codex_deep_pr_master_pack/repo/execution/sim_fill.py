"""execution/sim_fill.py

P0 execution fill simulator.

Deterministic knobs:
- latency sampled from execution.latency_model
- slippage estimated from either constant_bps or liquidity heuristic
- TTL can expire
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from integration.token_snapshot_store import TokenSnapshot
from execution.latency_model import LogNormalLatencyParams, sample_lognormal_ms


@dataclass(frozen=True)
class FillResult:
    status: str  # filled | partial | none
    fill_price: Optional[float]
    slippage_bps: Optional[float]
    latency_ms: int
    ttl_expired: bool


def simulate_fill(
    *,
    side: str,
    mid_price: float,
    size_usd: float,
    snapshot: Optional[TokenSnapshot],
    execution_cfg: Dict[str, Any],
    mode_ttl_sec: Optional[int],
    seed: Optional[int],
) -> FillResult:
    latency_cfg = (execution_cfg.get("latency") or {})
    enabled = bool(latency_cfg.get("enabled", True))
    latency_ms = 0
    if enabled:
        obs = latency_cfg.get("observe_delay_ms") or {}
        params = LogNormalLatencyParams(
            mean_ms=float(obs.get("mean", 250)),
            sigma=float(obs.get("sigma", 0.4)),
            clamp_min_ms=int(obs.get("clamp_min", 80)),
            clamp_max_ms=int(obs.get("clamp_max", 900)),
        )
        latency_ms = sample_lognormal_ms(params, seed=seed)

    ttl_cfg = (execution_cfg.get("orders") or {}).get("ttl") or {}
    default_ttl = int(ttl_cfg.get("default_ttl_sec", 120))
    ttl_sec = int(mode_ttl_sec) if mode_ttl_sec is not None else default_ttl
    ttl_expired = (latency_ms / 1000.0) > ttl_sec
    if ttl_expired:
        return FillResult(status="none", fill_price=None, slippage_bps=None, latency_ms=latency_ms, ttl_expired=True)

    slip_cfg = (execution_cfg.get("slippage_model") or {})
    model = slip_cfg.get("model", "constant_bps")
    constant_bps = float(slip_cfg.get("constant_bps", 80))
    impact_cap = float(slip_cfg.get("impact_cap_bps", 200))

    slippage_bps = constant_bps
    if model == "amm_xyk" and snapshot is not None and snapshot.liquidity_usd:
        ratio = max(size_usd, 0.0) / max(float(snapshot.liquidity_usd), 1.0)
        slippage_bps = min(impact_cap, ratio * impact_cap)

    fill_cfg = (execution_cfg.get("fill_model") or {})
    base_fill_rate = float(fill_cfg.get("base_fill_rate", 0.80))
    p = base_fill_rate
    p -= float(fill_cfg.get("penalty_per_1000ms_latency", 0.03)) * (latency_ms / 1000.0)
    p = max(min(p, 0.99), 0.01)

    # deterministic "coin flip" based on seed
    h = 0 if seed is None else int(seed) & 0xFFFFFFFF
    u = (h % 10_000) / 10_000.0
    if u > p:
        return FillResult(status="none", fill_price=None, slippage_bps=slippage_bps, latency_ms=latency_ms, ttl_expired=False)

    sign = 1.0 if side.upper() == "BUY" else -1.0
    fill_price = float(mid_price) * (1.0 + sign * (slippage_bps / 10_000.0))
    return FillResult(status="filled", fill_price=fill_price, slippage_bps=slippage_bps, latency_ms=latency_ms, ttl_expired=False)
