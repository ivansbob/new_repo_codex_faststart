# RUNBOOK — GMEE P0 (v0.4)

Этот runbook описывает операционные P0 процедуры:
- daily QA checks (data health),
- canary E2E replay,
- CI gates и критерии промоции (до business-code).

---

## 1) Daily QA (автоматически)

Источник: ClickHouse таблицы `trades`, `rpc_events`, `trade_attempts`, `forensics_events`.

### 1.1 Canonical time monotonicity

- Проверка: `signal_time ≤ entry_local_send_time ≤ entry_first_confirm_time`
- Любое нарушение должно порождать `forensics_events(kind='time_skew')`.
- Алерт: если `time_skew` > 0.1% от trades/day → STOP + расследование.

### 1.2 Null-rate / missing Tier-0 fields

Проверка доли NULL/дефолтов по ключевым полям (trades ядро):
- `trace_id, trade_id, chain, env, traced_wallet, buy_time, buy_price_usd, amount_usd`
- `entry_*` time chain
- `success_bool, failure_mode`

Алерт: >1% trades/day без Tier-0 → STOP.

### 1.3 Forensics spikes

Алерт на рост:
- `suspect_confirm`, `reorg`, `partial_confirm`, `schema_mismatch`
- Любой `crit` severity → STOP.

---

## 2) Canary E2E replay (каждый CI и регулярно в prod-env canary)

Скрипты:
- seed: `scripts/canary_golden_trace.sql`
- checks: `scripts/canary_checks.sql`

Проверяет:
- writer ordering не сломан
- MV наполняет `wallet_daily_agg_state`
- нет критических forensics по canary trace

---

## 3) Oracle test (exit-planner correctness)

Скрипт:
- dataset: `scripts/seed_golden_dataset.sql`
- запрос: `queries/04_glue_select.sql`

CI сравнивает TSV-строку с expected. Если oracle падает — нельзя менять planner/routing/параметры.

---

## 4) Promotion gates (до paper/live и до бизнес-кода)

Должно пройти:
1) Anti-drift (Variant A)
2) DDL apply
3) Query compile
4) Canary checks
5) Oracle test

---

## 5) Быстрый локальный чеклист

```bash
python3 scripts/assert_no_drift.py
docker exec -i ch clickhouse-client --multiquery < schemas/clickhouse.sql
docker exec -i ch clickhouse-client --multiquery < scripts/canary_golden_trace.sql
docker exec -i ch clickhouse-client --multiquery < scripts/canary_checks.sql
docker exec -i ch clickhouse-client --multiquery < scripts/seed_golden_dataset.sql
```
