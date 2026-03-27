#!/usr/bin/env python3
"""integration/paper_pipeline.py

Iteration-1 "paper runner" (P0.1): Trade → snapshot → gates → writes

What it does:
- Loads runtime config from strategy/config/params_base.yaml
- Writes forensics_events(kind="config_version") for reproducibility
- Consumes normalized Trade events from JSONL (offline replay)
- Enriches token gates via a local snapshot cache (Parquet) — no external APIs
- Applies hard gates
- For passing BUY trades:
  - inserts into signals_raw (via integration/write_signal.py helpers)
  - emits a minimal wallet_score event (for traceability)

P0.1 additions vs P0:
- JSONL parsing/validation moved into integration/trade_normalizer.py
- Token gates require a local snapshot (or inline values); missing snapshot => reject_reason=missing_snapshot
- End-of-run stats for reject reasons
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from dataclasses import replace
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Union

from integration.config_loader import load_params_base
from integration.mode_registry import resolve_modes
from integration.ch_client import ClickHouseConfig, make_runner
from integration.trade_types import Trade
from integration.trade_normalizer import load_trades_jsonl, normalize_trade_record
from integration.token_snapshot_store import TokenSnapshot, TokenSnapshotStore
from integration.run_trace import get_run_trace_id
from integration.gates import apply_gates
from integration.reject_reasons import INVALID_TRADE, MISSING_SNAPSHOT
from integration.parquet_io import ParquetReadConfig, iter_parquet_records
from integration.allowlist_loader import load_allowlist
from integration.wallet_profile_store import WalletProfileStore
from integration.wallet_tier_registry import resolve_tier

from integration.sim_preflight import preflight_and_simulate
from integration.execution_preflight import execution_preflight_and_simulate

from integration.write_signal import insert_signal
from integration.write_wallet_score import insert_wallet_score
from integration.write_trade_reject import insert_trade_reject


def _mk_allowlist_version_row(
    ts: str,
    chain: str,
    env: str,
    path: str,
    wallets_count: int,
    allowlist_hash: str,
    run_trace_id: str,
) -> Dict[str, Any]:
    """Run-level forensics event to version the active allowlist."""
    details = {"path": path, "wallets_count": wallets_count, "allowlist_hash": allowlist_hash}
    return {
        "event_id": str(uuid.uuid4()),
        "ts": ts,
        "chain": chain,
        "env": env,
        "kind": "allowlist_version",
        "severity": "info",
        "details_json": json.dumps(details, ensure_ascii=False, separators=(",", ":")),
        "trace_id": run_trace_id,
        "trade_id": None,
        "attempt_id": None,
    }


def _utc_now_iso_ms() -> str:
    # ClickHouse DateTime64(3) friendly format
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S.%f")[:23]


def _mk_config_version_row(
    ts: str,
    chain: str,
    env: str,
    path: str,
    strategy_name: str,
    version: str,
    config_hash: str,
    run_trace_id: str,
) -> Dict[str, Any]:
    return {
        "ts": ts,
        "chain": chain,
        "env": env,
        "kind": "config_version",
        "trace_id": run_trace_id,
        "payload_json": json.dumps(
            {
                "path": path,
                "strategy_name": strategy_name,
                "version": version,
                "config_hash": config_hash,
            },
            ensure_ascii=False,
        ),
    }


def _snapshot_from_trade_inline(trade: Trade) -> Optional[TokenSnapshot]:
    # If replay input already provides snapshot fields, we can use them for deterministic tests.
    if trade.liquidity_usd is None and trade.volume_24h_usd is None and trade.spread_bps is None:
        return None
    return TokenSnapshot(
        mint=trade.mint,
        ts_snapshot=None,
        liquidity_usd=trade.liquidity_usd,
        volume_24h_usd=trade.volume_24h_usd,
        spread_bps=trade.spread_bps,
        top10_holders_pct=None,
        single_holder_pct=None,
        extra=None,
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chain", default="solana")
    ap.add_argument("--env", default="paper")
    ap.add_argument("--run-trace-id", default="", help="Optional run trace id override (trace_id in CH == run_trace_id)")
    ap.add_argument("--config", default="strategy/config/params_base.yaml")
    ap.add_argument("--trades-jsonl", default="", help="Input trades in normalized JSONL (optional)")
    ap.add_argument(
        "--trades-parquet",
        default="",
        help="Input trades in Parquet (Data-track output). Requires duckdb (see requirements.txt).",
    )
    ap.add_argument(
        "--parquet-colmap-json",
        default="",
        help="Optional JSON mapping of target_col->source_col for parquet rename (e.g. {'ts':'block_ts'}).",
    )
    ap.add_argument("--parquet-limit", type=int, default=None, help="Optional limit for parquet replay")
    ap.add_argument(
        "--token-snapshot",
        default="integration/fixtures/token_snapshot.sample.csv",
        help="Local token snapshot cache (CSV/Parquet) for token gates (Data-track output)",
    )
    ap.add_argument(
        "--wallet-profiles",
        default="",
        help="Optional wallet profile cache (CSV/Parquet). If provided, missing wallet metrics in trades are enriched from it.",
    )
    ap.add_argument("--allowlist", default="strategy/wallet_allowlist.yaml", help="Allowlist file")
    ap.add_argument("--no-log-allowlist-version", action="store_true", help="Do not emit allowlist_version forensics event (run-level)")
    ap.add_argument("--require-allowlist", action="store_true", help="Fail if traced wallet not in allowlist")
    ap.add_argument("--source", default="paper_pipeline", help="signals_raw.source")
    ap.add_argument("--only-buy", action="store_true", help="Only create signals for BUY trades")
    ap.add_argument("--dry-run", action="store_true", help="Do not write to ClickHouse")
    ap.add_argument(
        "--summary-json",
        action="store_true",
        help="Print exactly one JSON line summary to stdout (logs go to stderr)",
    )
    ap.add_argument(
        "--sim-preflight",
        action="store_true",
        help="Attach deterministic sim_metrics (sim_metrics.v1) into --summary-json output (off by default)",
    )
    ap.add_argument(
        "--execution-preflight",
        action="store_true",
        help="Attach deterministic execution_metrics (execution_metrics.v1) into --summary-json output (off by default)",
    )
    ap.add_argument(
        "--metrics-out",
        default="",
        help="Write run metrics as JSON to this path (works in --dry-run too)",
    )
    args = ap.parse_args()

    def _log(msg: str) -> None:
        """Human logs.

        Contract:
        - If --summary-json is enabled, stdout must contain EXACTLY one JSON line
          (the summary) and nothing else. Therefore, all logs go to stderr.
        - Otherwise, logs go to stdout.
        """
        if args.summary_json:
            print(msg, file=sys.stderr)
        else:
            print(msg)

    ch_cfg = ClickHouseConfig()

    # Runner is only needed when writing to ClickHouse.
    runner = None
    if not args.dry_run:
        runner = make_runner(ch_cfg)

    loaded = load_params_base(args.config)
    cfg = loaded.config

    resolved_modes = resolve_modes(cfg)

    def pick_mode(explicit_mode: Optional[str]) -> str:
        """Assign a mode bucket for metrics, deterministically."""
        if explicit_mode:
            if explicit_mode in resolved_modes:
                return explicit_mode
            return "__unknown_mode__"
        if "U" in resolved_modes:
            return "U"
        if resolved_modes:
            return sorted(resolved_modes.keys())[0]
        return "__no_mode__"

    def _mc_bucket(mode: str) -> Dict[str, int]:
        return {
            "total_lines": 0,
            "normalized_ok": 0,
            "rejected_by_normalizer": 0,
            "rejected_by_gates": 0,
            "filtered_out": 0,
            "passed": 0,
        }

    mode_counts: Dict[str, Dict[str, int]] = defaultdict(_mc_bucket)

    run_trace_id = get_run_trace_id(args.run_trace_id or None, prefix="paper")

    # 1) config_version for reproducibility
    ts = _utc_now_iso_ms()
    row = _mk_config_version_row(
        ts=ts,
        chain=args.chain,
        env=args.env,
        path=loaded.path,
        strategy_name=loaded.strategy_name,
        version=loaded.version,
        config_hash=loaded.config_hash,
        run_trace_id=run_trace_id,
    )

    if args.dry_run:
        _log("[dry-run] would insert forensics_events(kind=config_version):")
        _log(json.dumps(row, ensure_ascii=False, indent=2))
    else:
        assert runner is not None
        runner.insert_json_each_row("forensics_events", [row])

    # 2) allowlist_version once per run_trace_id (avoid duplicate spam from per-row writers)
    if args.allowlist and not args.no_log_allowlist_version:
        wallets, allowlist_hash = load_allowlist(args.allowlist)
        allowlist_row = _mk_allowlist_version_row(
            ts=_utc_now_iso_ms(),
            chain=args.chain,
            env=args.env,
            path=args.allowlist,
            wallets_count=len(wallets),
            allowlist_hash=allowlist_hash,
            run_trace_id=run_trace_id,
        )
        if args.dry_run:
            _log("[dry-run] would insert forensics_events(kind=allowlist_version):")
            _log(json.dumps(allowlist_row, ensure_ascii=False, indent=2))
        else:
            assert runner is not None
            runner.insert_json_each_row("forensics_events", [allowlist_row])

    _log(f"[ok] wrote forensics_events config_version: {loaded.config_hash[:12]}… trace={run_trace_id}")

    # 2) Snapshot store (can be empty if file missing, but then gates will reject)
    store = TokenSnapshotStore(args.token_snapshot)
    try:
        store.load()
    except Exception as e:
        _log(f"[warn] failed to load token_snapshot parquet: {e}")

    # 2.5) Optional wallet profile store (for enrichment)
    wallet_store = None
    if args.wallet_profiles:
        try:
            if args.wallet_profiles.lower().endswith(".parquet"):
                wallet_store = WalletProfileStore.from_parquet(args.wallet_profiles)
            else:
                wallet_store = WalletProfileStore.from_csv(args.wallet_profiles)
            _log(f"[ok] loaded wallet_profiles: {len(getattr(wallet_store, '_by_wallet', {}))} wallets")
        except Exception as e:
            _log(f"[warn] failed to load wallet_profiles: {e}")

    # 3) Trades → snapshot → gates → writes
    if bool(args.trades_jsonl) == bool(args.trades_parquet):
        _log("[info] provide exactly one input: --trades-jsonl OR --trades-parquet. Done.")
        return 0

    # Build an iterator of Trade/Reject from either source.
    def _iter_inputs():
        if args.trades_jsonl:
            yield from load_trades_jsonl(args.trades_jsonl)
            return

        colmap = None
        if args.parquet_colmap_json:
            try:
                colmap_obj = json.loads(args.parquet_colmap_json)
                if not isinstance(colmap_obj, dict):
                    raise ValueError("colmap must be JSON object")
                colmap = colmap_obj
            except Exception as e:
                yield {"_reject": True, "lineno": 0, "reason": INVALID_TRADE, "detail": f"bad_parquet_colmap:{e}"}
                return

        pcfg = ParquetReadConfig(path=args.trades_parquet, limit=args.parquet_limit, colmap=colmap)
        for i, rec in enumerate(iter_parquet_records(pcfg), start=1):
            if not isinstance(rec, dict):
                yield {"_reject": True, "lineno": i, "reason": INVALID_TRADE, "detail": "parquet_row_not_dict"}
                continue
            yield normalize_trade_record(rec, lineno=i)

    total_lines = 0
    normalized_ok = 0
    rejected_by_normalizer = 0
    rejected_by_gates = 0
    filtered_out = 0
    passed = 0
    wrote_signals = 0
    wrote_scores = 0
    reject_counts: Counter[str] = Counter()

    mode_counts: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {
            "total_lines": 0,
            "normalized_ok": 0,
            "rejected_by_normalizer": 0,
            "rejected_by_gates": 0,
            "filtered_out": 0,
            "passed": 0,
        }
    )

    tier_counts: Dict[str, Dict[str, int]] = defaultdict(
        lambda: {
            "total_lines": 0,
            "normalized_ok": 0,
            "rejected_by_normalizer": 0,
            "rejected_by_gates": 0,
            "filtered_out": 0,
            "passed": 0,
        }
    )

    collect_for_post = bool(args.summary_json and (args.sim_preflight or args.execution_preflight))
    trades_norm_for_post = []  # Trade objects only (includes future ticks)

    for item in _iter_inputs():
        total_lines += 1

        explicit_mode: Optional[str] = None
        if isinstance(item, dict):
            m = item.get("mode")
            if isinstance(m, str):
                explicit_mode = m
        else:
            m = (item.extra or {}).get("mode") if hasattr(item, "extra") else None
            if isinstance(m, str):
                explicit_mode = m

        mode_bucket = pick_mode(explicit_mode)
        mode_counts[mode_bucket]["total_lines"] += 1

        # Tier bucketing is based on wallet_profiles (if available). For lines that
        # fail normalization, we fall back to the missing-wallet-profile bucket.
        wp_for_tier = None
        tier_bucket = "__missing_wallet_profile__"
        if isinstance(item, Trade) and wallet_store is not None:
            wp_for_tier = wallet_store.get(item.wallet)
            if wp_for_tier is not None:
                tier_bucket = resolve_tier(wp_for_tier, cfg)
        tier_counts[tier_bucket]["total_lines"] += 1

        if isinstance(item, dict) and item.get("_reject"):
            # Normalizer rejects are dicts; count + optionally emit as forensics.
            reason = str(item.get("reason", INVALID_TRADE))
            reject_counts[reason] += 1
            rejected_by_normalizer += 1
            mode_counts[mode_bucket]["rejected_by_normalizer"] += 1
            tier_counts[tier_bucket]["rejected_by_normalizer"] += 1

            if runner is not None:
                insert_trade_reject(
                    runner=runner,
                    chain=args.chain,
                    env=args.env,
                    trace_id=run_trace_id,
                    stage="normalizer",
                    reason=reason,
                    lineno=int(item.get("lineno")) if item.get("lineno") is not None else None,
                    wallet=None,
                    mint=None,
                    side=None,
                    tx_hash=str(item.get("tx_hash")) if item.get("tx_hash") else None,
                    detail=str(item.get("detail", "")) if item.get("detail") else None,
                    dry_run=False,
                )

            continue

        normalized_ok += 1
        mode_counts[mode_bucket]["normalized_ok"] += 1
        tier_counts[tier_bucket]["normalized_ok"] += 1
        t: Trade = item  # type: ignore

        # Optional enrichment from wallet_profiles (only fill missing metrics)
        if wallet_store is not None:
            wp = wp_for_tier if wp_for_tier is not None else wallet_store.get(t.wallet)
            if wp is not None:
                resolved_tier = resolve_tier(wp, cfg)
                t = replace(
                    t,
                    wallet_roi_30d_pct=t.wallet_roi_30d_pct if t.wallet_roi_30d_pct is not None else wp.roi_30d_pct,
                    wallet_winrate_30d=t.wallet_winrate_30d if t.wallet_winrate_30d is not None else wp.winrate_30d,
                    wallet_trades_30d=t.wallet_trades_30d if t.wallet_trades_30d is not None else wp.trades_30d,
                    extra=dict((t.extra or {}), **({"wallet_tier": resolved_tier})),
                )

        if collect_for_post:
            trades_norm_for_post.append(t)

        if args.only_buy and t.side != "BUY":
            # Filtering is not a rejection. Track separately so metrics remain meaningful.
            filtered_out += 1
            mode_counts[mode_bucket]["filtered_out"] += 1
            tier_counts[tier_bucket]["filtered_out"] += 1
            continue

        # Prefer inline snapshot, else pull from local store
        snap = _snapshot_from_trade_inline(t) or store.get(t.mint)

        decision = apply_gates(cfg=cfg, trade=t, snapshot=snap)
        if not decision.passed:
            reject_counts[decision.primary_reason or "rejected"] += 1
            rejected_by_gates += 1
            mode_counts[mode_bucket]["rejected_by_gates"] += 1
            tier_counts[tier_bucket]["rejected_by_gates"] += 1
            # Emit queryable reject event (CH only)
            if runner is not None:
                insert_trade_reject(
                    runner=runner,
                    chain=args.chain,
                    env=args.env,
                    trace_id=run_trace_id,
                    stage="gates",
                    reason=str(decision.primary_reason or "rejected"),
                    lineno=None,
                    wallet=t.wallet,
                    mint=t.mint,
                    side=t.side,
                    tx_hash=t.tx_hash or None,
                    detail=str(decision.detail) if getattr(decision, "detail", None) else None,
                    dry_run=False,
                )
            continue

        passed += 1
        mode_counts[mode_bucket]["passed"] += 1
        tier_counts[tier_bucket]["passed"] += 1

        pool_id = t.pool_id or ""
        payload = {
            "trade_ts": t.ts,
            "trade_tx": t.tx_hash,
            "trade_side": t.side,
            "trade_price": t.price,
            "trade_size_usd": t.size_usd,
            "platform": t.platform,
            "run_trace_id": run_trace_id,
        }

        # Include minimal snapshot fields for debugging
        if snap is not None:
            payload.update(
                {
                    "snapshot_liquidity_usd": snap.liquidity_usd,
                    "snapshot_volume_24h_usd": snap.volume_24h_usd,
                    "snapshot_spread_bps": snap.spread_bps,
                }
            )

        # IMPORTANT: In --dry-run we must stay fully deterministic and keep stdout clean
        # for --summary-json. Do NOT call insert_signal/insert_wallet_score in dry-run,
        # because their helpers print human output.
        if not args.dry_run:
            insert_signal(
                cfg=ch_cfg,
                chain=args.chain,
                env=args.env,
                source=args.source,
                traced_wallet=t.wallet,
                token_mint=t.mint,
                pool_id=pool_id,
                ts=_utc_now_iso_ms(),
                trace_id=run_trace_id,
                signal_id="",
                payload=payload,
                allowlist_path=args.allowlist,
                require_allowlist=bool(args.require_allowlist),
                log_allowlist_version=False,
                dry_run=False,
            )
        wrote_signals += 1

        # Minimal wallet_score (P0.1: placeholder constant, but wired end-to-end)
        score = 0.5
        features = {"runner": "paper_pipeline", "run_trace_id": run_trace_id}
        if not args.dry_run:
            insert_wallet_score(
                cfg=ch_cfg,
                chain=args.chain,
                env=args.env,
                traced_wallet=t.wallet,
                score=score,
                features=features,
                ts=_utc_now_iso_ms(),
                trace_id=run_trace_id,
                trade_id=t.tx_hash,
                attempt_id="",
                allowlist_path=args.allowlist,
                log_allowlist_version=False,
                dry_run=False,
            )
        wrote_scores += 1

    summary = {
        "ok": True,
        "run_trace_id": run_trace_id,
        "input": {"kind": "jsonl" if args.trades_jsonl else "parquet", "path": args.trades_jsonl or args.trades_parquet},
        "counts": {
            "total_lines": total_lines,
            "normalized_ok": normalized_ok,
            "rejected_by_normalizer": rejected_by_normalizer,
            "rejected_by_gates": rejected_by_gates,
            "filtered_out": filtered_out,
            "passed": passed,
            "signals_written": wrote_signals,
            "wallet_scores_written": wrote_scores,
        },
        "rejects": dict(reject_counts),
    }

    # Normalize defaultdict to plain dict for JSON.
    summary["mode_counts"] = {k: dict(v) for k, v in mode_counts.items()}
    summary["tier_counts"] = {k: dict(v) for k, v in tier_counts.items()}

    if args.summary_json and args.sim_preflight:
        summary["sim_metrics"] = preflight_and_simulate(
            trades_norm=trades_norm_for_post,
            cfg=cfg,
            token_snapshot_store=store,
            wallet_profile_store=wallet_store,
        )

    if args.summary_json and args.execution_preflight:
        # Convert snapshot store -> mint->dict mapping expected by execution_preflight.
        token_snap_map: Dict[str, dict] = {}
        for t in trades_norm_for_post:
            mint = t.mint
            if mint in token_snap_map:
                continue
            snap = _snapshot_from_trade_inline(t) or store.get(mint)
            if snap is None:
                continue
            token_snap_map[mint] = {
                "mint": mint,
                "spread_bps": snap.spread_bps,
                "liquidity_usd": snap.liquidity_usd,
                "volume_24h_usd": snap.volume_24h_usd,
            }

        trades_as_dicts = [
            {
                "ts": t.ts,
                "wallet": t.wallet,
                "mint": t.mint,
                "side": t.side,
                "price": t.price,
            }
            for t in trades_norm_for_post
        ]

        summary["execution_metrics"] = execution_preflight_and_simulate(
            trades_norm=trades_as_dicts,
            token_snapshot=token_snap_map,
            cfg=cfg,
        )

    if args.metrics_out:
        try:
            with open(args.metrics_out, "w", encoding="utf-8") as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
        except Exception as e:
            _log(f"[warn] failed to write metrics_out={args.metrics_out}: {e}")

    if args.summary_json:
        # Exactly one JSON line on stdout.
        print(json.dumps(summary, ensure_ascii=False, separators=(",", ":")))
    else:
        _log(
            "[summary] "
            f"total_lines={total_lines} "
            f"normalized_ok={normalized_ok} "
            f"rejected_by_normalizer={rejected_by_normalizer} "
            f"rejected_by_gates={rejected_by_gates} "
            f"trades_passed_gates={passed} "
            f"signals_written={wrote_signals} "
            f"wallet_scores_written={wrote_scores} "
            f"run_trace_id={run_trace_id}"
        )

        if reject_counts:
            _log("[reject_reasons]")
            for reason, cnt in reject_counts.most_common(10):
                _log(f"  - {reason}: {cnt}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
