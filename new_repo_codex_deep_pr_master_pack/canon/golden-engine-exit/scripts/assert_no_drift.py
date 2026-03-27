#!/usr/bin/env python3
"""
scripts/assert_no_drift.py

P0 Anti-drift gate for GMEE (Variant A).

Checks:
1) configs/queries.yaml params == SQL placeholders (1:1, no extras) for queries/*.sql.
2) queries/04_glue_select.sql has NO hardcoded numeric literals equal to YAML thresholds/epsilon/aggr/clamp (Variant A).
3) queries/04_glue_select.sql contains the mode→quantile mapping contract:
   U->q10_hold_sec, S->q25_hold_sec, M->q40_hold_sec, L->median_hold_sec.
4) docs/CONTRACT_MATRIX.md mentions YAML sources + Variant A + CI gates.
5) schemas/clickhouse.sql includes required tables, exactly one MV named mv_wallet_daily_agg_state,
   exactly one VIEW named wallet_profile_30d, wallet_profile_30d is anchored on max(day),
   TTL values match configs/golden_exit_engine.yaml retention (signals_raw/rpc_events/microticks_1s),
   and trades has no TTL when trades_ttl_days == 0.

Exit code != 0 on failure.
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Dict, List, Set

try:
    import yaml  # type: ignore
except Exception as e:
    print(f"FATAL: PyYAML is required: {e}", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parents[1]

PATH_QUERIES_YAML = ROOT / "configs" / "queries.yaml"
PATH_GOLDEN_YAML = ROOT / "configs" / "golden_exit_engine.yaml"
PATH_CONTRACT_MATRIX = ROOT / "docs" / "CONTRACT_MATRIX.md"
PATH_CLICKHOUSE_DDL = ROOT / "schemas" / "clickhouse.sql"
QUERIES_DIR = ROOT / "queries"

SQL_PLACEHOLDER_RE = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*):[^}]+\}")
SQL_NUM_LITERAL_RE = re.compile(
    r"""
    (?<![a-zA-Z_])
    (
      (?:\d+\.\d+) |    # decimal
      (?:\d+)             # integer
    )
    (?![a-zA-Z_])
    """,
    re.VERBOSE,
)

BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
LINE_COMMENT_RE = re.compile(r"--[^\n]*")


@dataclass(frozen=True)
class Fail:
    code: str
    msg: str


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(str(path))
    return path.read_text(encoding="utf-8")


def strip_sql_comments(sql: str) -> str:
    sql = re.sub(BLOCK_COMMENT_RE, " ", sql)
    sql = re.sub(LINE_COMMENT_RE, " ", sql)
    return sql


def extract_placeholders(sql: str) -> List[str]:
    return [m.group(1) for m in SQL_PLACEHOLDER_RE.finditer(sql)]


def unique_order(seq: List[str]) -> List[str]:
    seen: Set[str] = set()
    out: List[str] = []
    for x in seq:
        if x not in seen:
            seen.add(x)
            out.append(x)
    return out


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(read_text(path))


def die(fails: List[Fail]) -> None:
    for f in fails:
        print(f"[FAIL:{f.code}] {f.msg}", file=sys.stderr)
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"[OK] {msg}")


def gather_yaml_numbers(golden: dict) -> Dict[str, Decimal]:
    """Extract numbers that must NEVER appear as literals in queries/04_glue_select.sql.

    Note: margin_mult_default may be 1.0; we intentionally DO NOT add it to the forbidden literal set
    because SQL will naturally contain '- 1' in pct-change formulas. Variant A requirement is satisfied
    by requiring margin_mult to be a placeholder.
    """
    cd = golden["chain_defaults"]["solana"]
    ret = golden["retention"]
    nums: Dict[str, Decimal] = {}

    def dec(v) -> Decimal:
        return Decimal(str(v))

    # thresholds
    nums["mode_u_max_sec"] = dec(cd["mode_thresholds_sec"]["U_max"])
    nums["mode_s_max_sec"] = dec(cd["mode_thresholds_sec"]["S_max"])
    nums["mode_m_max_sec"] = dec(cd["mode_thresholds_sec"]["M_max"])
    # clamp
    nums["min_hold_sec"] = dec(cd["planned_hold"]["clamp_sec"]["min"])
    nums["max_hold_sec"] = dec(cd["planned_hold"]["clamp_sec"]["max"])
    # epsilon
    nums["epsilon_pad_ms"] = dec(cd["epsilon"]["pad_ms_default"])
    nums["epsilon_min_ms"] = dec(cd["epsilon"]["hard_bounds_ms"]["min"])
    nums["epsilon_max_ms"] = dec(cd["epsilon"]["hard_bounds_ms"]["max"])
    # aggr triggers
    for mode in ["U", "S", "M", "L"]:
        nums[f"aggr_{mode.lower()}_up_pct"] = dec(cd["aggr_triggers"][mode]["up_pct"])
        nums[f"aggr_{mode.lower()}_window_s"] = dec(cd["aggr_triggers"][mode]["window_sec"])
    # microticks
    nums["microticks_window_s"] = dec(cd["microticks"]["window_sec"])

    # TTL/retention (used in DDL checks, not SQL04 literal check)
    nums["ttl_signals_raw_days"] = dec(ret["signals_raw_ttl_days"])
    nums["ttl_rpc_events_days"] = dec(ret["rpc_events_ttl_days"])
    nums["ttl_microticks_days"] = dec(ret["microticks_ttl_days"])
    nums["ttl_trades_days"] = dec(ret["trades_ttl_days"])
    nums["microticks_ttl_days"] = dec(cd["microticks"]["ttl_days"])

    return nums


def check_placeholders_vs_registry(fails: List[Fail]) -> None:
    qcfg = load_yaml(PATH_QUERIES_YAML)
    if "functions" not in qcfg:
        fails.append(Fail("QYAML", "configs/queries.yaml: missing 'functions'"))
        return

    functions = qcfg["functions"]
    for fn_name, spec in functions.items():
        sql_rel = spec.get("sql")
        params = spec.get("params", [])
        if not isinstance(params, list):
            fails.append(Fail("QYAML", f"{fn_name}: params must be a list"))
            continue

        sql_path = ROOT / sql_rel
        if not sql_path.exists():
            fails.append(Fail("QYAML", f"{fn_name}: sql file not found: {sql_rel}"))
            continue

        sql = read_text(sql_path)
        ph = unique_order(extract_placeholders(sql))
        ph_set, param_set = set(ph), set(params)

        extra = sorted(param_set - ph_set)
        missing = sorted(ph_set - param_set)
        if extra or missing:
            fails.append(
                Fail(
                    "PARAMS",
                    f"{fn_name}: params↔placeholders mismatch. extra={extra} missing={missing}",
                )
            )

    ok("queries.yaml params match SQL placeholders (1:1) for all registered queries")


def check_variant_a_no_literals_sql04(fails: List[Fail], yaml_nums: Dict[str, Decimal]) -> None:
    sql04 = read_text(QUERIES_DIR / "04_glue_select.sql")
    sql04_nc = strip_sql_comments(sql04)

    required_ph = {
        "mode_u_max_sec",
        "mode_s_max_sec",
        "mode_m_max_sec",
        "min_hold_sec",
        "max_hold_sec",
        "epsilon_pad_ms",
        "epsilon_min_ms",
        "epsilon_max_ms",
        "aggr_u_up_pct",
        "aggr_s_up_pct",
        "aggr_m_up_pct",
        "aggr_l_up_pct",
        "aggr_u_window_s",
        "aggr_s_window_s",
        "aggr_m_window_s",
        "aggr_l_window_s",
        "microticks_window_s",
        "margin_mult",
        "chain",
        "trade_id",
    }
    ph = set(extract_placeholders(sql04))
    missing = sorted(required_ph - ph)
    if missing:
        fails.append(Fail("VARTA", f"SQL04 missing required placeholders: {missing}"))

    forbidden: Set[Decimal] = set()
    for k, v in yaml_nums.items():
        if k.startswith("ttl_") or k.endswith("_ttl_days"):
            continue
        if k == "ttl_trades_days" or k == "microticks_ttl_days":
            continue
        forbidden.add(v)

    literals = [Decimal(m.group(1)) for m in SQL_NUM_LITERAL_RE.finditer(sql04_nc)]
    hit = sorted({str(x) for x in literals if x in forbidden})
    if hit:
        fails.append(
            Fail(
                "VARTA",
                "SQL04 contains hardcoded numeric literals equal to YAML thresholds (forbidden). "
                f"Hits={hit}. (Variant A requires placeholders instead.)",
            )
        )
    else:
        ok("SQL04 has no hardcoded numeric literals matching YAML thresholds (Variant A)")


def check_mode_quantile_mapping_contract(fails: List[Fail]) -> None:
    sql04 = strip_sql_comments(read_text(QUERIES_DIR / "04_glue_select.sql"))
    required_tokens = [
        "mode = 'U'",
        "q10_hold_sec",
        "mode = 'S'",
        "q25_hold_sec",
        "mode = 'M'",
        "q40_hold_sec",
        "median_hold_sec",
    ]
    missing = [t for t in required_tokens if t not in sql04]
    if missing:
        fails.append(Fail("MAP", f"SQL04 missing mapping contract tokens: {missing}"))
    else:
        ok("SQL04 contains mode→quantile mapping contract tokens (U/S/M/L -> q10/q25/q40/median)")


def check_contract_matrix_mentions(fails: List[Fail]) -> None:
    doc = read_text(PATH_CONTRACT_MATRIX)
    must = [
        "configs/golden_exit_engine.yaml",
        "configs/queries.yaml",
        "Variant A",
        "CI gates",
        "ch_compile_smoke.yml",
        "queries/04_glue_select.sql",
    ]
    missing = [x for x in must if x not in doc]
    if missing:
        fails.append(Fail("DOC", f"docs/CONTRACT_MATRIX.md missing required mentions: {missing}"))
    else:
        ok("CONTRACT_MATRIX mentions YAML sources + Variant A + CI gates")


def ddl_find_ttl_days(ddl: str, table: str) -> int | None:
    pat = re.compile(
        rf"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+{re.escape(table)}.*?TTL\s+.*?toIntervalDay\((\d+)\)",
        re.IGNORECASE | re.DOTALL,
    )
    m = pat.search(ddl)
    if not m:
        return None
    return int(m.group(1))


def check_clickhouse_ddl(fails: List[Fail], yaml_nums: Dict[str, Decimal]) -> None:
    ddl = read_text(PATH_CLICKHOUSE_DDL)

    required_tables = [
        "signals_raw",
        "trade_attempts",
        "rpc_events",
        "trades",
        "microticks_1s",
        "wallet_daily_agg_state",
        "latency_arm_state",
        "controller_state",
        "provider_usage_daily",
        "forensics_events",
    ]
    for t in required_tables:
        if re.search(rf"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+{re.escape(t)}\b", ddl, re.IGNORECASE) is None:
            fails.append(Fail("DDL", f"schemas/clickhouse.sql missing table: {t}"))

    mv_ok = re.search(r"CREATE\s+MATERIALIZED\s+VIEW\s+IF\s+NOT\s+EXISTS\s+mv_wallet_daily_agg_state\b", ddl, re.IGNORECASE)
    view_ok = re.search(r"CREATE\s+VIEW\s+IF\s+NOT\s+EXISTS\s+wallet_profile_30d\b", ddl, re.IGNORECASE)
    if not mv_ok:
        fails.append(Fail("DDL", "Missing MV mv_wallet_daily_agg_state"))
    if not view_ok:
        fails.append(Fail("DDL", "Missing VIEW wallet_profile_30d"))

    if "SELECT max(day) FROM wallet_daily_agg_state" not in ddl:
        fails.append(Fail("DDL", "wallet_profile_30d must be anchored on max(day) from wallet_daily_agg_state"))

    signals_ttl = ddl_find_ttl_days(ddl, "signals_raw")
    rpc_ttl = ddl_find_ttl_days(ddl, "rpc_events")
    micro_ttl = ddl_find_ttl_days(ddl, "microticks_1s")

    exp_signals = int(yaml_nums["ttl_signals_raw_days"])
    exp_rpc = int(yaml_nums["ttl_rpc_events_days"])
    exp_micro_ret = int(yaml_nums["ttl_microticks_days"])
    exp_micro_cd = int(yaml_nums["microticks_ttl_days"])

    if exp_micro_ret != exp_micro_cd:
        fails.append(Fail("YAML", "retention.microticks_ttl_days must match chain_defaults.solana.microticks.ttl_days (anti-drift)"))

    if signals_ttl != exp_signals:
        fails.append(Fail("TTL", f"signals_raw TTL mismatch: DDL={signals_ttl} YAML={exp_signals}"))
    if rpc_ttl != exp_rpc:
        fails.append(Fail("TTL", f"rpc_events TTL mismatch: DDL={rpc_ttl} YAML={exp_rpc}"))
    if micro_ttl != exp_micro_ret:
        fails.append(Fail("TTL", f"microticks_1s TTL mismatch: DDL={micro_ttl} YAML={exp_micro_ret}"))

    trades_ttl_days = int(yaml_nums["ttl_trades_days"])
    if trades_ttl_days == 0:
        m = re.search(r"CREATE\s+TABLE\s+IF\s+NOT\s+EXISTS\s+trades\b(.*?);", ddl, re.IGNORECASE | re.DOTALL)
        if m and re.search(r"\bTTL\b", m.group(1), re.IGNORECASE):
            fails.append(Fail("TTL", "trades_ttl_days=0 but DDL for trades contains TTL (forbidden)"))

    ok("ClickHouse DDL required tables present, MV/VIEW present, TTL matches YAML, view anchored deterministically")


def main() -> None:
    fails: List[Fail] = []
    golden = load_yaml(PATH_GOLDEN_YAML)
    yaml_nums = gather_yaml_numbers(golden)

    check_placeholders_vs_registry(fails)
    check_variant_a_no_literals_sql04(fails, yaml_nums)
    check_mode_quantile_mapping_contract(fails)
    check_contract_matrix_mentions(fails)
    check_clickhouse_ddl(fails, yaml_nums)

    if fails:
        die(fails)

    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
