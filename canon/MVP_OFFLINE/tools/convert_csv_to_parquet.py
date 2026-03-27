#!/usr/bin/env python3
"""Convert a CSV matching INPUT_CONTRACT.md into Parquet.

This is intentionally tiny and optional. It requires `pyarrow` installed locally:
  python -m pip install pyarrow
"""

from __future__ import annotations

import argparse
import sys

import pandas as pd


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="Path to input CSV")
    ap.add_argument("--parquet", required=True, help="Path to output Parquet")
    args = ap.parse_args()

    df = pd.read_csv(args.csv)
    # Normalize timestamp column to timezone-aware UTC
    df["ts"] = pd.to_datetime(df["ts"], utc=True)
    df.to_parquet(args.parquet, index=False)
    print(f"Wrote {args.parquet} rows={len(df)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
