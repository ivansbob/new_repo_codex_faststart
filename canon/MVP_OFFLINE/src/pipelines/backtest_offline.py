from __future__ import annotations

import argparse
from typing import Dict, List

import pandas as pd

from ..utils.config import load_yaml
from ..core.types import Trade, WalletProfile, TokenState
from ..strategy.signal_engine import build_signal
from ..strategy.risk_engine import PortfolioState, compute_position_size_usd, allow_new_position
from ..execution.simulator import run_simulation


def df_to_trades(df: pd.DataFrame) -> List[Trade]:
    out: List[Trade] = []
    for r in df.itertuples(index=False):
        out.append(
            Trade(
                ts=pd.to_datetime(getattr(r, "ts"), utc=True).to_pydatetime(),
                wallet=str(getattr(r, "wallet")),
                token_mint=str(getattr(r, "token_mint")),
                side=str(getattr(r, "side")).lower(),
                price=float(getattr(r, "price")),
                size_usd=float(getattr(r, "size_usd")),
                size_token=float(getattr(r, "size_token", 0.0) or 0.0),
                platform=str(getattr(r, "platform", "other")).lower(),
                tx_hash=str(getattr(r, "tx_hash", "")),
                pool_address=(None if pd.isna(getattr(r, "pool_address", None)) or str(getattr(r, "pool_address", "")).strip()=="" else str(getattr(r, "pool_address"))),
                slot=int(getattr(r, "slot", 0) or 0),
            )
        )
    out.sort(key=lambda x: x.ts)
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--trades", required=True, help="data/processed/trades.parquet or .csv")
    ap.add_argument("--config", required=True, help="config/params_mvp.yaml")
    ap.add_argument("--bankroll", type=float, default=10_000.0)
    args = ap.parse_args()

    cfg: Dict = load_yaml(args.config)

    if args.trades.endswith(".parquet"):
        df = pd.read_parquet(args.trades)
    else:
        df = pd.read_csv(args.trades)

    trades = df_to_trades(df)

    # MVP: wallet profiles are defaults (replace with real wallet_profiles later)
    wp_map: Dict[str, WalletProfile] = {}
    for w, g in df.groupby("wallet"):
        wp_map[w] = WalletProfile(
            wallet=str(w),
            roi_30d=float(cfg["defaults"]["wallet_roi_30d"]),
            winrate=float(cfg["defaults"]["wallet_winrate"]),
            trades_30d=int(cfg["defaults"]["wallet_trades_30d"]),
            median_hold_sec=float(cfg["defaults"]["wallet_median_hold_sec"]),
            avg_size_usd=float(g["size_usd"].mean()),
            tier=str(cfg["defaults"]["wallet_tier"]),
        )

    port = PortfolioState(bankroll_usd=float(args.bankroll))
    signals = []

    for t in trades:
        wp = wp_map.get(t.wallet)
        if wp is None:
            continue

        # MVP: token state is defaults (replace with real token snapshots later)
        ts = TokenState(
            token_mint=t.token_mint,
            price=float(t.price),
            liquidity_usd=float(cfg["defaults"]["token_liquidity_usd"]),
            spread_bps=float(cfg["defaults"]["token_spread_bps"]),
            honeypot_flag=False,
        )

        sig = build_signal(trade=t, wp=wp, ts=ts, leader_entry_ts=t.ts, cfg=cfg)
        if sig is None:
            continue

        size = compute_position_size_usd(port.bankroll_usd, cfg)
        if not allow_new_position(port, t.token_mint, size, cfg):
            continue

        sig.size_usd = size
        signals.append(sig)

        port.open_positions += 1
        port.exposure_by_token[t.token_mint] = port.exposure_by_token.get(t.token_mint, 0.0) + size

    res = run_simulation(signals, trades, cfg)
    total = float(res.total_pnl_usd)
    roi = (total / float(args.bankroll)) if args.bankroll else 0.0

    print(f"Signals: {len(signals)}")
    print(f"Positions: {len(res.positions)}")
    print(f"Total PnL USD: {total:,.2f}")
    print(f"ROI: {roi*100:.2f}%")
    print("Exit reasons:", pd.Series([p.exit_reason for p in res.positions]).value_counts().to_dict())


if __name__ == "__main__":
    main()
