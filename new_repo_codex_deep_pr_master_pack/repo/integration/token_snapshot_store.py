"""integration/token_snapshot_store.py

Local snapshot cache for token/pool metrics used by gates and (later) features.

P0.1 goals:
- No external API calls.
- Deterministic: read a local snapshot file produced by Data-track.
- Zero required dependencies: CSV is supported out of the box.
- Parquet is supported *optionally* if the environment has a reader (pandas+pyarrow/fastparquet).
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class TokenSnapshot:
    mint: str
    ts_snapshot: Optional[str] = None
    liquidity_usd: Optional[float] = None
    volume_24h_usd: Optional[float] = None
    spread_bps: Optional[float] = None
    top10_holders_pct: Optional[float] = None
    single_holder_pct: Optional[float] = None
    extra: Optional[Dict[str, Any]] = None


class TokenSnapshotStore:
    """Loads token snapshots from a local file into an in-memory map."""

    def __init__(self, path: str):
        self.path = str(path)
        self._by_mint: Dict[str, TokenSnapshot] = {}

    # ------------------------------------------------------------------
    # Compatibility constructors (used by tools/ scripts)
    # ------------------------------------------------------------------
    @classmethod
    def from_csv(cls, path: str) -> "TokenSnapshotStore":
        """Load a snapshot store from a CSV file.

        This is a thin wrapper kept for backward compatibility with tooling
        (e.g. dataset exporter) that expects `from_csv`.
        """
        store = cls(path)
        store.load()
        return store

    @classmethod
    def from_parquet(cls, path: str) -> "TokenSnapshotStore":
        """Load a snapshot store from a Parquet file.

        This is a thin wrapper kept for backward compatibility with tooling
        (e.g. dataset exporter) that expects `from_parquet`.
        """
        store = cls(path)
        store.load()
        return store

    def load(self) -> None:
        path = Path(self.path)
        if not path.exists():
            return

        rows = _read_snapshot_rows(path)
        if not rows:
            return

        # Keep latest per mint if ts_snapshot is present (string-sorted).
        # Data-track should ideally emit ISO timestamps.
        latest: Dict[str, Dict[str, Any]] = {}
        for r in rows:
            mint = str(r.get("mint", "")).strip()
            if not mint:
                continue
            prev = latest.get(mint)
            if prev is None:
                latest[mint] = r
                continue
            ts_prev = str(prev.get("ts_snapshot") or "")
            ts_cur = str(r.get("ts_snapshot") or "")
            if ts_cur >= ts_prev:
                latest[mint] = r

        for mint, r in latest.items():
            self._by_mint[mint] = TokenSnapshot(
                mint=mint,
                ts_snapshot=_opt_str(r.get("ts_snapshot")),
                liquidity_usd=_opt_float(r.get("liquidity_usd")),
                volume_24h_usd=_opt_float(r.get("volume_24h_usd")),
                spread_bps=_opt_float(r.get("spread_bps")),
                top10_holders_pct=_opt_float(r.get("top10_holders_pct")),
                single_holder_pct=_opt_float(r.get("single_holder_pct")),
                extra=None,
            )

    def get(self, mint: str) -> Optional[TokenSnapshot]:
        return self._by_mint.get(mint)

    def get_latest(self, mint: str) -> Optional[TokenSnapshot]:
        """Alias for get().

        The store keeps only the latest snapshot per mint when loading.
        Some callers use the more explicit name `get_latest`.
        """
        return self.get(mint)

def _read_snapshot_rows(path: Path) -> list[Dict[str, Any]]:
    ext = path.suffix.lower()
    if ext in {".parquet", ".pq"}:
        # Optional Parquet support
        try:
            import pandas as pd  # type: ignore
            df = pd.read_parquet(path)
            return df.to_dict(orient="records")
        except Exception:
            # Fall back to sibling CSV if present
            csv_path = path.with_suffix(".csv")
            if csv_path.exists():
                return _read_snapshot_rows(csv_path)
            raise

    # Default: CSV
    with open(path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [dict(row) for row in reader]


def _opt_float(x) -> Optional[float]:
    if x is None:
        return None
    s = str(x).strip()
    if s == "":
        return None
    try:
        return float(s)
    except Exception:
        return None


def _opt_str(x) -> Optional[str]:
    if x is None:
        return None
    s = str(x)
    return s if s != "" else None
