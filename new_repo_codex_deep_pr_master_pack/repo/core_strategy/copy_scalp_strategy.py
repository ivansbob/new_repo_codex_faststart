"""
strategy.py — "one-formula" spec implementation (entry decision + regime overlay + sizing + execution params)

This file is intentionally dependency-light: it defines the canonical decision flow and interfaces
you can wire to your ingestion / feature builder / ML model / simulator.

Key idea:
wallet BUY event -> hard gates -> features -> p_model -> EV -> polymarket regime r
-> dynamic thresholds -> risk sizing/limits -> Signal (ENTER/SKIP) with mode + order params.

Aggressive layer:
NOT an entry selector. It is a post-entry position management switch (partial + runner + trailing)
triggered by fast price impulse and guarded by safety gates & aggr limits.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple, Literal


Decision = Literal["ENTER", "SKIP"]
ModeBase = Literal["U", "S", "M", "L"]
ModeActive = str  # e.g. "U_base", "S_aggr"


# -----------------------------
# Core state objects (minimal)
# -----------------------------

@dataclass(frozen=True)
class WalletProfile:
    wallet: str
    roi_30d: float
    winrate_30d: float
    trades_30d: int
    avg_hold_sec: float
    max_dd_30d: float = 0.0
    avg_trade_size_usd: float = 0.0
    tier: str = "tier2"              # tier0/tier1/tier2
    dex_pref: Optional[str] = None   # raydium/jupiter/pumpfun/...


@dataclass(frozen=True)
class TokenSnapshot:
    mint: str
    price: float
    ret_1m: float = 0.0
    ret_5m: float = 0.0
    vol_5m: float = 0.0
    liquidity_usd: float = 0.0
    volume_24h: float = 0.0
    spread_bps: float = 0.0
    honeypot_safe: bool = True

    # Optional: provide a function or a precomputed estimate for slippage at some size.
    # If you don't have it, keep None and the strategy will use a simple heuristic.
    slippage_est_bps_for_1k: Optional[float] = None  # "bps per $1k" rough slope


@dataclass(frozen=True)
class PolymarketSnapshot:
    # User-defined normalization: bullish in [0..1], event risk in [0..1]
    pm_bullish_score: float
    pm_event_risk: float


@dataclass(frozen=True)
class WalletBuyEvent:
    ts: datetime
    wallet: str
    mint: str
    entry_price: float           # price observed at event time (or quote mid)
    platform: str = "other"
    tx_hash: str = ""


@dataclass
class PortfolioState:
    bankroll_usd: float
    open_positions: int = 0
    daily_pnl_usd: float = 0.0
    total_drawdown_pct: float = 0.0
    exposure_by_token: Dict[str, float] = field(default_factory=dict)
    exposure_by_source_wallet: Dict[str, float] = field(default_factory=dict)
    cooldown_active: bool = False
    aggr_trades_today: int = 0
    aggr_open_positions: int = 0
    aggr_exposure_usd: float = 0.0


@dataclass(frozen=True)
class Signal:
    decision: Decision
    reason: str

    ts: datetime
    wallet: str
    mint: str

    # scoring
    r_regime: float
    p_model: float
    ev: float

    # mode & execution
    mode_base: Optional[ModeBase] = None
    mode_active: Optional[ModeActive] = None
    size_usd: float = 0.0
    ttl_sec: int = 0
    tp_pct: float = 0.0
    sl_pct: float = 0.0
    max_slippage_bps: int = 0
    limit_price_buffer_bps: int = 0


# -----------------------------
# Interfaces you plug in
# -----------------------------

class FeatureBuilder:
    def build(self, W: WalletProfile, M: TokenSnapshot, P: PolymarketSnapshot) -> Dict[str, float]:
        """
        Return a flat dict of features x = Φ(W,M,P) to feed the model.
        Implement this in src/models/feature_builder.py
        """
        # minimal fallback: just a few obvious signals
        return {
            "w_roi_30d": W.roi_30d,
            "w_winrate_30d": W.winrate_30d,
            "w_trades_30d": float(W.trades_30d),
            "w_avg_hold_sec": W.avg_hold_sec,
            "m_liquidity_usd": M.liquidity_usd,
            "m_spread_bps": M.spread_bps,
            "m_ret_1m": M.ret_1m,
            "m_ret_5m": M.ret_5m,
            "m_vol_5m": M.vol_5m,
            "pm_bullish": P.pm_bullish_score,
            "pm_event_risk": P.pm_event_risk,
        }


class CalibratedModel:
    def predict_proba(self, x: Dict[str, float]) -> float:
        """
        Return calibrated probability p_model in [0..1].
        Implement in src/models/ml_model.py
        """
        # placeholder: do NOT use in production
        # This just maps roi/winrate/liquidity into a stable number.
        base = 0.50
        base += 0.10 * max(0.0, min(1.0, x.get("w_winrate_30d", 0.5) - 0.5))
        base += 0.10 * max(0.0, min(1.0, x.get("w_roi_30d", 0.0)))
        base += 0.05 * max(0.0, min(1.0, (x.get("m_liquidity_usd", 0.0) / 50_000.0)))
        return float(max(0.0, min(1.0, base)))


# -----------------------------
# Strategy params (single place)
# -----------------------------

@dataclass(frozen=True)
class StrategyParams:
    # Polymarket regime scalar: r in [-1..+1]
    pm_a: float = 1.0
    pm_b: float = 1.0

    # Hard gates
    min_trades_30d: int = 50
    min_winrate_30d: float = 0.60
    min_roi_30d: float = 0.25
    min_liquidity_usd: float = 15_000.0
    max_spread_bps: float = 200.0
    require_honeypot_safe: bool = True

    # Dynamic thresholds vs regime
    p0: float = 0.58
    k_p: float = 0.03
    delta0: float = 0.00
    k_delta: float = 0.01

    # Expected payoff (μ_win, μ_loss) per base mode (in % as decimals)
    payoff_mu_win: Dict[str, float] = field(default_factory=lambda: {"U": 0.03, "S": 0.05, "M": 0.09, "L": 0.14})
    payoff_mu_loss: Dict[str, float] = field(default_factory=lambda: {"U": 0.025, "S": 0.045, "M": 0.07, "L": 0.10})

    # Costs (bps)
    fee_bps: float = 30.0
    latency_bps: float = 60.0  # proxy for adverse selection due to delay
    # slippage is computed from snapshot via estimate_slippage_bps()

    # Mode selection by wallet avg_hold_sec
    hold_thresh_U: float = 35.0
    hold_thresh_S: float = 130.0
    hold_thresh_M: float = 220.0

    # Base mode specs (ttl, tp, sl)
    mode_ttl: Dict[str, int] = field(default_factory=lambda: {"U": 30, "S": 90, "M": 180, "L": 300})
    mode_tp: Dict[str, float] = field(default_factory=lambda: {"U": 0.03, "S": 0.05, "M": 0.09, "L": 0.14})
    mode_sl: Dict[str, float] = field(default_factory=lambda: {"U": -0.025, "S": -0.045, "M": -0.07, "L": -0.10})

    # Aggressive triggers (post-entry)
    aggr_enabled: bool = True
    aggr_triggers: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "U_aggr": {"base": "U", "dt_sec_max": 12, "min_chg_pct": 0.03},
        "S_aggr": {"base": "S", "dt_sec_max": 30, "min_chg_pct": 0.06},
        "M_aggr": {"base": "M", "dt_sec_max": 60, "min_chg_pct": 0.10},
        "L_aggr": {"base": "L", "dt_sec_max": 90, "min_chg_pct": 0.15},
    })
    # Aggressive profile behavior (runner + trailing) — used by executor/simulator
    aggr_profiles: Dict[str, Dict[str, Any]] = field(default_factory=lambda: {
        "U_aggr": {"partial_pct": 0.40, "trail_from_peak_pct": 0.12, "tp2_pct": 0.20, "sl2_pct": -0.06},
        "S_aggr": {"partial_pct": 0.50, "trail_from_peak_pct": 0.12, "tp2_pct": 0.50, "sl2_pct": -0.12},
        "M_aggr": {"partial_pct": 0.40, "trail_from_peak_pct": 0.15, "tp2_pct": 1.00, "sl2_pct": -0.20},
        "L_aggr": {"partial_pct": 0.35, "trail_from_peak_pct": 0.18, "tp2_pct": 2.00, "sl2_pct": -0.30},
    })

    # Aggressive safety gates (stricter than base)
    aggr_min_roi_30d: float = 0.25
    aggr_min_winrate_30d: float = 0.60
    aggr_allowed_tiers: Tuple[str, ...] = ("tier0", "tier1")
    aggr_min_liquidity_usd: float = 20_000.0
    aggr_max_spread_bps: float = 150.0

    # Aggressive limits
    max_aggr_trades_per_day: int = 10
    max_aggr_open_positions: int = 3
    max_aggr_exposure_pct: float = 0.08
    aggr_size_multiplier_vs_base: float = 0.75

    # Sizing vs regime
    s0_pct: float = 0.01
    k_s: float = 0.5
    min_pos_pct: float = 0.005
    max_pos_pct: float = 0.02

    # Position limits vs regime
    M0: int = 20
    k_m: float = 0.5
    max_exposure_per_token_pct: float = 0.10
    max_exposure_per_wallet_source_pct: float = 0.12
    max_daily_loss_pct: float = 0.07
    max_total_dd_pct: float = 0.25

    # Execution params
    max_slippage_bps: int = 200
    limit_price_buffer_bps: int = 50


# -----------------------------
# Strategy implementation
# -----------------------------

class CopyScalpStrategy:
    def __init__(
        self,
        params: StrategyParams,
        feature_builder: Optional[FeatureBuilder] = None,
        model: Optional[CalibratedModel] = None,
    ):
        self.p = params
        self.feature_builder = feature_builder or FeatureBuilder()
        self.model = model or CalibratedModel()

    # ---- Polymarket overlay ----

    def polymarket_regime(self, P: PolymarketSnapshot) -> float:
        """
        r(t) = clip( a*(2*bullish-1) - b*event_risk, -1, +1)
        """
        bullish_component = self.p.pm_a * (2.0 * float(P.pm_bullish_score) - 1.0)
        risk_component = self.p.pm_b * float(P.pm_event_risk)
        r = bullish_component - risk_component
        return float(max(-1.0, min(1.0, r)))

    def p_min(self, r: float) -> float:
        # risk-off (r<0) -> raise p_min
        return float(self.p.p0 + self.p.k_p * (-r))

    def delta_ev(self, r: float) -> float:
        # risk-off -> demand higher EV cushion
        return float(self.p.delta0 + self.p.k_delta * (-r))

    # ---- Hard gates ----

    def passes_hard_gates(self, W: WalletProfile, M: TokenSnapshot) -> Tuple[bool, str]:
        if W.trades_30d < self.p.min_trades_30d:
            return False, "wallet_trades_30d_low"
        if W.winrate_30d < self.p.min_winrate_30d:
            return False, "wallet_winrate_low"
        if W.roi_30d < self.p.min_roi_30d:
            return False, "wallet_roi_low"
        if M.liquidity_usd < self.p.min_liquidity_usd:
            return False, "token_liquidity_low"
        if M.spread_bps > self.p.max_spread_bps:
            return False, "token_spread_high"
        if self.p.require_honeypot_safe and (not M.honeypot_safe):
            return False, "honeypot_flag"
        return True, "ok"

    # ---- Mode selection ----

    def choose_base_mode(self, W: WalletProfile) -> ModeBase:
        h = float(W.avg_hold_sec)
        if h <= self.p.hold_thresh_U:
            return "U"
        if h <= self.p.hold_thresh_S:
            return "S"
        if h <= self.p.hold_thresh_M:
            return "M"
        return "L"

    # ---- Cost / EV ----

    def estimate_slippage_bps(self, M: TokenSnapshot, size_usd: float) -> float:
        """
        Minimal heuristic:
        - if slippage slope provided: slope_bps_per_$1k * (size_usd/1000)
        - else: (size/liquidity)*10_000 * c  (c ~= 0.5)
        """
        if M.slippage_est_bps_for_1k is not None:
            return float(M.slippage_est_bps_for_1k) * max(0.0, size_usd / 1000.0)
        if M.liquidity_usd <= 0:
            return 10_000.0
        c = 0.5
        return float(min(10_000.0, (size_usd / M.liquidity_usd) * 10_000.0 * c))

    def expected_payoff(self, mode: ModeBase) -> Tuple[float, float]:
        mu_win = float(self.p.payoff_mu_win.get(mode, 0.05))
        mu_loss = float(self.p.payoff_mu_loss.get(mode, 0.05))
        return mu_win, mu_loss

    def compute_ev(self, p_model: float, mode: ModeBase, cost_pct: float) -> float:
        mu_win, mu_loss = self.expected_payoff(mode)
        # EV = p*mu_win - (1-p)*mu_loss - cost
        return float(p_model * mu_win - (1.0 - p_model) * mu_loss - cost_pct)

    # ---- Sizing / limits ----

    def size_pct(self, r: float) -> float:
        # size_pct(r)=clamp(s0*(1+k_s*r), 0.5%, 2%)
        raw = self.p.s0_pct * (1.0 + self.p.k_s * r)
        return float(max(self.p.min_pos_pct, min(self.p.max_pos_pct, raw)))

    def max_open_positions(self, r: float) -> int:
        # max_open_positions(r)=round(M0*(1+k_m*r))
        raw = self.p.M0 * (1.0 + self.p.k_m * r)
        return int(max(1, round(raw)))

    def risk_limits_ok(self, port: PortfolioState, r: float, mint: str, source_wallet: str, size_usd: float) -> Tuple[bool, str]:
        # kill-switch style checks
        if port.daily_pnl_usd <= -abs(port.bankroll_usd * self.p.max_daily_loss_pct):
            return False, "daily_loss_limit"
        if port.total_drawdown_pct >= self.p.max_total_dd_pct:
            return False, "total_drawdown_kill"
        if port.cooldown_active:
            return False, "cooldown_active"

        # position count adjusted by regime
        if port.open_positions >= self.max_open_positions(r):
            return False, "max_open_positions"

        # exposure caps
        token_cap = port.bankroll_usd * self.p.max_exposure_per_token_pct
        cur_tok = port.exposure_by_token.get(mint, 0.0)
        if cur_tok + size_usd > token_cap:
            return False, "token_exposure_cap"

        wallet_cap = port.bankroll_usd * self.p.max_exposure_per_wallet_source_pct
        cur_src = port.exposure_by_source_wallet.get(source_wallet, 0.0)
        if cur_src + size_usd > wallet_cap:
            return False, "source_wallet_exposure_cap"

        return True, "ok"

    # ---- Entry decision ----

    def decide_on_wallet_buy(
        self,
        event: WalletBuyEvent,
        W: WalletProfile,
        M: TokenSnapshot,
        P: PolymarketSnapshot,
        port: PortfolioState,
    ) -> Signal:
        # 1) hard gates
        ok, why = self.passes_hard_gates(W, M)
        if not ok:
            return Signal(
                decision="SKIP", reason=why,
                ts=event.ts, wallet=event.wallet, mint=event.mint,
                r_regime=0.0, p_model=0.0, ev=0.0,
            )

        # 2) regime scalar r
        r = self.polymarket_regime(P)

        # 3) choose base mode
        mode = self.choose_base_mode(W)

        # 4) build features and predict p_model
        x = self.feature_builder.build(W=W, M=M, P=P)
        p_model = float(self.model.predict_proba(x))

        # 5) sizing (depends on r)
        size_usd = float(port.bankroll_usd * self.size_pct(r))

        # 6) costs (as pct) = fees + spread + slippage(size) + latency
        sl_bps = self.estimate_slippage_bps(M, size_usd)
        cost_bps = float(self.p.fee_bps + float(M.spread_bps) + sl_bps + self.p.latency_bps)
        cost_pct = cost_bps / 10_000.0

        # 7) EV
        ev = self.compute_ev(p_model=p_model, mode=mode, cost_pct=cost_pct)

        # 8) dynamic thresholds
        pmin = self.p_min(r)
        delta = self.delta_ev(r)

        if (p_model < pmin) or (ev < delta):
            return Signal(
                decision="SKIP",
                reason="ev_or_p_below_threshold",
                ts=event.ts, wallet=event.wallet, mint=event.mint,
                r_regime=r, p_model=p_model, ev=ev,
            )

        # 9) portfolio / risk limits
        ok2, why2 = self.risk_limits_ok(port, r=r, mint=event.mint, source_wallet=event.wallet, size_usd=size_usd)
        if not ok2:
            return Signal(
                decision="SKIP",
                reason=why2,
                ts=event.ts, wallet=event.wallet, mint=event.mint,
                r_regime=r, p_model=p_model, ev=ev,
            )

        # 10) finalize execution params
        ttl = int(self.p.mode_ttl[mode])
        tp = float(self.p.mode_tp[mode])
        sl = float(self.p.mode_sl[mode])

        return Signal(
            decision="ENTER",
            reason="ok",
            ts=event.ts, wallet=event.wallet, mint=event.mint,
            r_regime=r, p_model=p_model, ev=ev,
            mode_base=mode,
            mode_active=f"{mode}_base",
            size_usd=size_usd,
            ttl_sec=ttl,
            tp_pct=tp,
            sl_pct=sl,
            max_slippage_bps=int(self.p.max_slippage_bps),
            limit_price_buffer_bps=int(self.p.limit_price_buffer_bps),
        )

    # ---- Aggressive layer (post-entry) ----

    def passes_aggressive_safety(self, W: WalletProfile, M: TokenSnapshot, port: PortfolioState) -> Tuple[bool, str]:
        if not self.p.aggr_enabled:
            return False, "aggr_disabled"
        if W.roi_30d < self.p.aggr_min_roi_30d:
            return False, "aggr_wallet_roi_low"
        if W.winrate_30d < self.p.aggr_min_winrate_30d:
            return False, "aggr_wallet_winrate_low"
        if W.tier not in self.p.aggr_allowed_tiers:
            return False, "aggr_wallet_tier_block"
        if M.liquidity_usd < self.p.aggr_min_liquidity_usd:
            return False, "aggr_liquidity_low"
        if M.spread_bps > self.p.aggr_max_spread_bps:
            return False, "aggr_spread_high"
        if self.p.require_honeypot_safe and (not M.honeypot_safe):
            return False, "aggr_honeypot_flag"

        # aggr limits
        if port.aggr_trades_today >= self.p.max_aggr_trades_per_day:
            return False, "aggr_daily_trade_limit"
        if port.aggr_open_positions >= self.p.max_aggr_open_positions:
            return False, "aggr_open_positions_limit"
        if port.aggr_exposure_usd >= port.bankroll_usd * self.p.max_aggr_exposure_pct:
            return False, "aggr_exposure_limit"

        # portfolio risk state
        if port.cooldown_active:
            return False, "aggr_cooldown_active"
        if port.daily_pnl_usd <= -abs(port.bankroll_usd * self.p.max_daily_loss_pct):
            return False, "aggr_daily_loss_limit"
        if port.total_drawdown_pct >= self.p.max_total_dd_pct:
            return False, "aggr_total_dd_kill"

        return True, "ok"

    def maybe_switch_to_aggressive(
        self,
        mode_base: ModeBase,
        dt_sec: int,
        price_change: float,
        W: WalletProfile,
        M: TokenSnapshot,
        port: PortfolioState,
        follow_on_smart_money: bool = False,
    ) -> Tuple[Optional[str], str]:
        """
        Returns (new_mode_active, reason). If None -> no switch.
        Intended to be called from simulator/executor on each tick until partial is taken.
        """
        ok, why = self.passes_aggressive_safety(W, M, port)
        if not ok:
            return None, why

        for name, trig in self.p.aggr_triggers.items():
            if trig["base"] != mode_base:
                continue
            if dt_sec > int(trig["dt_sec_max"]):
                continue
            if price_change < float(trig["min_chg_pct"]):
                continue
            if name == "M_aggr" and trig.get("require_follow_on_smart_money", False):
                if not follow_on_smart_money:
                    continue
            return name, "aggr_triggered"

        return None, "no_change"

    def aggressive_profile(self, mode_active: str) -> Dict[str, Any]:
        """
        Return partial/trailing runner profile (tp2/sl2/trail) for executor.
        """
        return dict(self.p.aggr_profiles.get(mode_active, {}))


# -----------------------------
# Minimal demo usage (optional)
# -----------------------------

def _demo():
    from datetime import datetime

    params = StrategyParams()
    strat = CopyScalpStrategy(params)

    port = PortfolioState(bankroll_usd=10_000.0)

    event = WalletBuyEvent(ts=datetime.utcnow(), wallet="w1", mint="m1", entry_price=1.0)
    W = WalletProfile(wallet="w1", roi_30d=0.35, winrate_30d=0.65, trades_30d=120, avg_hold_sec=70, tier="tier1")
    M = TokenSnapshot(mint="m1", price=1.0, liquidity_usd=30_000, spread_bps=120, honeypot_safe=True, slippage_est_bps_for_1k=20)
    P = PolymarketSnapshot(pm_bullish_score=0.65, pm_event_risk=0.20)

    sig = strat.decide_on_wallet_buy(event, W, M, P, port)
    print(sig)

if __name__ == "__main__":
    _demo()
