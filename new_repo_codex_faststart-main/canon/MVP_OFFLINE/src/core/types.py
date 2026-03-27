from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Optional

Side = Literal["buy", "sell"]
Platform = Literal["raydium", "jupiter", "pumpfun", "meteora", "other"]


@dataclass(frozen=True)
class Trade:
    # Normalized on-chain event
    ts: datetime
    wallet: str
    token_mint: str
    side: Side

    # Offline MVP keeps price on the event to allow simulation without external price feeds.
    price: float        # token price in USD at the event timestamp
    size_usd: float     # trade notional in USD (or an estimate)

    # Optional / enrichment fields (kept for compatibility with “боевой” blueprint)
    size_token: float = 0.0
    platform: Platform = "other"
    tx_hash: str = ""
    pool_address: Optional[str] = None
    slot: int = 0


@dataclass(frozen=True)
class WalletProfile:
    wallet: str
    roi_30d: float
    winrate: float
    trades_30d: int
    median_hold_sec: float
    avg_size_usd: float

    # Extended (boilerplate defaults for MVP_OFFLINE)
    roi_90d: float = 0.0
    preferred_dex: Platform = "other"
    role: str = "unknown"   # "sniper" | "deployer" | "follower" | ...
    tier: str = "tier2"


@dataclass(frozen=True)
class TokenState:
    token_mint: str
    price: float
    liquidity_usd: float

    # Offline MVP uses spread as a proxy for execution quality
    spread_bps: float

    # Extended token snapshot fields (defaults in MVP_OFFLINE)
    volume_5m: float = 0.0
    volume_30m: float = 0.0
    depth_1pct: float = 0.0
    depth_5pct: float = 0.0
    honeypot_flag: bool = False


@dataclass
class Signal:
    trade: Trade
    wallet_profile: WalletProfile
    token_state: TokenState

    # ML outputs (optional; rule-based MVP keeps 0.0)
    p_model: float = 0.0
    edge: float = 0.0
    risk_regime: float = 0.0  # overlay scalar [-1..+1]

    # Strategy decision
    mode: str = "U_base"     # e.g. "U_base", "S_aggr"
    size_usd: float = 0.0
    ttl_sec: int = 60

    # Exit parameters (simple defaults, overridden by mode config)
    tp_pct: float = 0.02
    sl_pct: float = 0.01


@dataclass
class Position:
    id: str
    signal: Signal
    entry_ts: datetime
    entry_price: float
    size_usd: float
    peak_price: float
    remaining_usd: float

    # Token-based bookkeeping (useful for partial exits; kept optional for MVP_OFFLINE)
    size_tokens: float = 0.0
    remaining_size: float = 0.0

    realized_pnl_usd: float = 0.0
    is_closed: bool = False
    exit_ts: Optional[datetime] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    partial_taken: bool = False
    partial_size_pct: float = 0.0
    mode_base: str = ""
    mode_active: str = ""
    aggr_locked_out_reason: str = ""
