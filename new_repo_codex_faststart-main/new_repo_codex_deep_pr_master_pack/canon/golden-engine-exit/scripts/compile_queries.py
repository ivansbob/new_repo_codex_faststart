#!/usr/bin/env python3
"""Compile the canonical SQL queries with EXPLAIN SYNTAX.

This script is intentionally small and deterministic. It reads
configs/golden_exit_engine.yaml to build a complete set of params for
ClickHouse named placeholders ({name:Type}).

It executes inside the ClickHouse docker-compose service to avoid
requiring clickhouse-client on the host.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception as e:  # pragma: no cover
    print("ERROR: pyyaml is required. Install with: pip install pyyaml", file=sys.stderr)
    raise


ROOT = Path(__file__).resolve().parents[1]


def build_params(chain: str = "solana") -> dict[str, object]:
    golden = yaml.safe_load((ROOT / "configs" / "golden_exit_engine.yaml").read_text(encoding="utf-8"))
    cd = golden["chain_defaults"][chain]

    # Dummy values (only for compilation):
    wallet = "wallet_ci_dummy"
    trade_id = "00000000-0000-0000-0000-000000000011"

    return {
        "chain": chain,
        "wallet": wallet,
        "trade_id": trade_id,
        "window_s": int(cd["microticks"]["window_sec"]),
        "microticks_window_s": int(cd["microticks"]["window_sec"]),
        "min_hold_sec": int(cd["planned_hold"]["clamp_sec"]["min"]),
        "max_hold_sec": int(cd["planned_hold"]["clamp_sec"]["max"]),
        "mode_u_max_sec": int(cd["mode_thresholds_sec"]["U_max"]),
        "mode_s_max_sec": int(cd["mode_thresholds_sec"]["S_max"]),
        "mode_m_max_sec": int(cd["mode_thresholds_sec"]["M_max"]),
        "margin_mult": float(cd["planned_hold"]["margin_mult_default"]),
        "epsilon_pad_ms": int(cd["epsilon"]["pad_ms_default"]),
        "epsilon_min_ms": int(cd["epsilon"]["hard_bounds_ms"]["min"]),
        "epsilon_max_ms": int(cd["epsilon"]["hard_bounds_ms"]["max"]),
        "aggr_u_up_pct": float(cd["aggr_triggers"]["U"]["up_pct"]),
        "aggr_s_up_pct": float(cd["aggr_triggers"]["S"]["up_pct"]),
        "aggr_m_up_pct": float(cd["aggr_triggers"]["M"]["up_pct"]),
        "aggr_l_up_pct": float(cd["aggr_triggers"]["L"]["up_pct"]),
        "aggr_u_window_s": int(cd["aggr_triggers"]["U"]["window_sec"]),
        "aggr_s_window_s": int(cd["aggr_triggers"]["S"]["window_sec"]),
        "aggr_m_window_s": int(cd["aggr_triggers"]["M"]["window_sec"]),
        "aggr_l_window_s": int(cd["aggr_triggers"]["L"]["window_sec"]),
    }


def run_clickhouse(query: str, params: dict[str, object]) -> None:
    flags = [f"--param_{k}={v}" for k, v in params.items()]
    cmd = [
        "docker",
        "compose",
        "exec",
        "-T",
        "clickhouse",
        "clickhouse-client",
        "--query",
        query,
        *flags,
    ]
    subprocess.check_call(cmd, cwd=str(ROOT))


def main() -> int:
    params = build_params("solana")
    queries = [
        ROOT / "queries" / "01_profile_query.sql",
        ROOT / "queries" / "02_routing_query.sql",
        ROOT / "queries" / "03_microticks_window.sql",
        ROOT / "queries" / "04_glue_select.sql",
    ]

    for q in queries:
        sql = q.read_text(encoding="utf-8")
        run_clickhouse(f"EXPLAIN SYNTAX {sql}", params)

    print("[compile] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
