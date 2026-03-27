#!/usr/bin/env bash
set -euo pipefail

# Local smoke runner that mirrors the CI gates.
# CI remains the source of truth; this script is for fast local validation.

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

require() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "[smoke] missing required command: $1" >&2
    exit 1
  }
}

require docker
require python3

echo "[smoke] starting ClickHouse via docker compose..."
docker compose up -d

echo "[smoke] waiting for ClickHouse..."
for i in $(seq 1 60); do
  if docker compose exec -T clickhouse clickhouse-client --format=Null --query "SELECT 1" >/dev/null 2>&1; then
    echo "[smoke] ClickHouse is ready"
    break
  fi
  sleep 1
  if [ "$i" = "60" ]; then
    echo "[smoke] ClickHouse did not become ready" >&2
    exit 1
  fi
done

echo "[smoke] apply ClickHouse DDL"
docker compose exec -T clickhouse clickhouse-client --multiquery < schemas/clickhouse.sql

echo "[smoke] anti-drift gate"
python3 scripts/assert_no_drift.py

echo "[smoke] compile queries (EXPLAIN SYNTAX)"
python3 scripts/compile_queries.py

echo "[smoke] canary seed + checks"
docker compose exec -T clickhouse clickhouse-client --multiquery < scripts/canary_golden_trace.sql
# NOTE: fixed typo here; must be 'docker', not 'ndocker'.
docker compose exec -T clickhouse clickhouse-client --multiquery < scripts/canary_checks.sql

echo "[smoke] oracle seed"
docker compose exec -T clickhouse clickhouse-client --multiquery < scripts/seed_golden_dataset.sql

echo "[smoke] oracle glue_select parity"
out_file="/tmp/gmee_oracle_out.tsv"
python3 scripts/run_oracle_glue_select.py > "$out_file"
diff -u scripts/oracle_expected.tsv "$out_file"

echo "[smoke] OK"
