#!/usr/bin/env python3
"""Run the canonical oracle query (queries/04_glue_select.sql) and print TSVRaw.

P0 rule: this runner must be *registry-driven*.
- Parameter *names* come from configs/queries.yaml (functions.glue_select.params)
- Parameter *values* come from configs/golden_exit_engine.yaml (chain_defaults.<chain> ...)
- Extra or missing params are a hard error (exit!=0)

Execution:
- Uses `docker compose exec clickhouse clickhouse-client` to avoid requiring a host install.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parent.parent


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_registry_params() -> list[str]:
    reg = _load_yaml(ROOT / "configs" / "queries.yaml")
    return list(reg["functions"]["glue_select"]["params"])


def load_chain_defaults(chain: str) -> dict[str, Any]:
    cfg = _load_yaml(ROOT / "configs" / "golden_exit_engine.yaml")
    try:
        return cfg["chain_defaults"][chain]
    except KeyError as e:
        raise SystemExit(f"Unknown chain in configs/golden_exit_engine.yaml: {chain}") from e


def build_params(chain: str, trade_id: str) -> dict[str, str]:
    """Build params for SQL04 strictly by registry."""
    cd = load_chain_defaults(chain)

    clamp = cd["planned_hold"]["clamp_sec"]
    eps = cd["epsilon"]
    mt = cd["microticks"]
    ag = cd["aggr_triggers"]
    modes = cd["mode_thresholds_sec"]

    # Map config -> placeholder names (Variant A; overlay v2 naming)
    computed: dict[str, str] = {
        "chain": chain,
        "trade_id": trade_id,
        "min_hold_sec": str(int(clamp["min"])),
        "max_hold_sec": str(int(clamp["max"])),
        "margin_mult": str(float(cd["planned_hold"]["margin_mult_default"])),
        "epsilon_pad_ms": str(int(eps["pad_ms_default"])),
        "epsilon_min_ms": str(int(eps["hard_bounds_ms"]["min"])),
        "epsilon_max_ms": str(int(eps["hard_bounds_ms"]["max"])),
        "microticks_window_s": str(int(mt["window_sec"])),
        "mode_u_max_sec": str(int(modes["U_max"])),
        "mode_s_max_sec": str(int(modes["S_max"])),
        "mode_m_max_sec": str(int(modes["M_max"])),
        "aggr_u_up_pct": str(float(ag["U"]["up_pct"])),
        "aggr_s_up_pct": str(float(ag["S"]["up_pct"])),
        "aggr_m_up_pct": str(float(ag["M"]["up_pct"])),
        "aggr_l_up_pct": str(float(ag["L"]["up_pct"])),
        "aggr_u_window_s": str(int(ag["U"]["window_sec"])),
        "aggr_s_window_s": str(int(ag["S"]["window_sec"])),
        "aggr_m_window_s": str(int(ag["M"]["window_sec"])),
        "aggr_l_window_s": str(int(ag["L"]["window_sec"])),
    }

    required = load_registry_params()
    missing = [k for k in required if k not in computed]
    extra = [k for k in computed.keys() if k not in required]

    if missing or extra:
        print("ERROR: param set mismatch (registry-driven strict mode)", file=sys.stderr)
        if missing:
            print("  missing:", ", ".join(missing), file=sys.stderr)
        if extra:
            print("  extra:", ", ".join(extra), file=sys.stderr)
        raise SystemExit(2)

    # Stable order (helps debugging)
    return {k: computed[k] for k in required}


def run_clickhouse(sql_path: Path, params: dict[str, str]) -> str:
    sql = sql_path.read_text(encoding="utf-8")
    cmd = [
        "docker",
        "compose",
        "exec",
        "-T",
        "clickhouse",
        "clickhouse-client",
        "--multiquery",
        "--format",
        "TSVRaw",
    ]
    for k, v in params.items():
        cmd.append(f"--param_{k}={v}")
    cmd.append("--query")
    cmd.append(sql)
    r = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True)
    if r.returncode != 0:
        sys.stderr.write(r.stderr)
        raise SystemExit(r.returncode)
    return r.stdout


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--chain", default="solana")
    ap.add_argument(
        "--trade-id",
        default="00000000000000000000000000000011",
        help="trade_id present in scripts/seed_golden_dataset.sql",
    )
    args = ap.parse_args()
    params = build_params(args.chain, args.trade_id)
    sql_path = ROOT / "queries" / "04_glue_select.sql"
    sys.stdout.write(run_clickhouse(sql_path, params))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
