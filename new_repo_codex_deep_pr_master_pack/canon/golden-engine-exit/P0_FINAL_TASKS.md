# P0_FINAL_TASKS — GMEE v0.4.1 (Variant A)

Цель: втянуть P0-каркас GMEE в основное репо так, чтобы **бизнес-код писался только поверх контрактов**, а CI ловил любой drift между **YAML ↔ SQL ↔ DDL ↔ docs**.

**P0 scope:** contracts + storage + canary + CI gates + Tier-0 writer + planner glue (через SQL).
**Запрещено в P0:** P1/P2 (bandit/ε-jobs, probation/rollback автоматика, новые ML фичи, мультичейн-адаптеры как продуктовая фича, Tier-2/MEV фиды, дорогие подписки).

---

## 0) P0 Definition of Done (DoD)

P0 закрыт, когда в **main-repo**:

1) Миграции применимы автоматически (dev + CI):
- ClickHouse: `schemas/clickhouse.sql`
- Postgres: `schemas/postgres.sql`

2) CI gates обязательны на PR и зелёные:
- DDL apply на пустой ClickHouse
- `EXPLAIN SYNTAX` на `queries/01..04.sql`
- `python3 scripts/assert_no_drift.py`
- canary: `scripts/canary_golden_trace.sql` + `scripts/canary_checks.sql`
- oracle: `scripts/seed_golden_dataset.sql` + запуск `queries/04_glue_select.sql` + сравнение TSV с expected

3) В коде main-repo реализованы:
- Tier‑0 writer с **writer ordering** (см. SPEC)
- `compute_exit_plan()` **строго через** `queries/04_glue_select.sql` (Variant A)
- запись в `trades` полей планировщика из результата `glue_select`

---

## 1) Встроить артефакты P0 в main-repo (без правок)

**Сделать:**
- добавить папку `gmee/` (или иной префикс) с:
  - `docs/` (SPEC/DATA_MODEL/CONTRACT_MATRIX/RUNBOOK)
  - `configs/` (golden_exit_engine.yaml, queries.yaml)
  - `schemas/` (clickhouse.sql, postgres.sql)
  - `queries/` (01..04.sql)
  - `scripts/` (assert_no_drift.py, canary_*.sql, seed_golden_dataset.sql)
  - `.github/workflows/` (шаги smoke можно встроить в существующий CI)

**Acceptance:**
- содержимое совпадает с P0-пакетом (без “улучшений от себя”);
- любые изменения этих файлов возможны только через PR с зелёным CI.

---

## 2) Миграции / инфраструктура БД

### 2.1 ClickHouse
**Сделать:**
- добавить миграционный шаг/джобу: применить `schemas/clickhouse.sql` на пустой БД
- обеспечить идемпотентность (можно прогонять повторно)

**Acceptance:**
- на чистой БД создаются:
  - таблицы: `signals_raw, trade_attempts, rpc_events, trades, microticks_1s, wallet_daily_agg_state, latency_arm_state, controller_state, provider_usage_daily, forensics_events`
  - MV `mv_wallet_daily_agg_state`
  - VIEW `wallet_profile_30d`
- TTL совпадает с YAML (это проверяет anti-drift)

### 2.2 Postgres
**Сделать:**
- добавить миграционный шаг: применить `schemas/postgres.sql`

**Acceptance:**
- созданы: `config_store, experiment_registry, promotions_audit` + индексы

---

## 3) Подключить CI gates (обязательные)

**Сделать:**
- добавить в CI (или переиспользовать `ch_compile_smoke.yml`) шаги:
  1. `python3 scripts/assert_no_drift.py`
  2. поднять ClickHouse
  3. применить DDL
  4. `EXPLAIN SYNTAX` для `queries/01..04.sql` (с dummy params)
  5. canary seed + checks
  6. oracle seed + запуск `04_glue_select.sql` + строгий compare TSV

**Acceptance:**
- CI обязателен для merge
- oracle expected строка совпадает 1:1

---

## 4) Tier‑0 writer (P0 бизнес-код)

### 4.1 Writer ordering (строго)
**Сделать:**
- реализовать writer, который **всегда** пишет события в порядке:
  `signals_raw → trade_attempts → rpc_events → trades → microticks_1s`

**Acceptance:**
- canary-подобная транзакция в коде воспроизводит canary invariants (см. canary_checks.sql)

### 4.2 Must-log IDs и инварианты
**Сделать:**
- всегда заполнять: `trace_id, trade_id, attempt_id, idempotency_token, experiment_id, config_hash, env, chain`
- enforce monotonicity:
  `signal_time ≤ entry_local_send_time ≤ entry_first_confirm_time`
- при нарушении — писать `forensics_events(kind='time_skew', severity='crit'|'warn')`

**Acceptance:**
- нарушения фиксируются форензикой (и легко находятся по trace_id)

### 4.3 Idempotency contract (attempt rules)
**Сделать:**
- новый `attempt_id` только если меняется **одно из**:
  - `payload_hash`
  - `nonce_scope/nonce_value`
  - `stage` (entry→exit)
- иначе retry увеличивает `attempt_no/retry_count`, но `attempt_id` сохраняется

**Acceptance:**
- повторы не раздувают attempts “по каждому ретраю” новым attempt_id

---

## 5) Planner P0: compute_exit_plan() (SQL parity)

### 5.1 Реализация
**Сделать:**
- `compute_exit_plan(chain, trade_id)` выполняет `queries/04_glue_select.sql` в ClickHouse
- **НЕ реализует математику порогов вручную**
- параметры берутся из `configs/golden_exit_engine.yaml` и передаются как `{param:Type}`

**Возвращает ровно:**
`mode, planned_hold_sec, epsilon_ms, planned_exit_ts, aggr_flag`

**Acceptance:**
- в oracle-test (seed + query) результат совпадает с expected TSV

### 5.2 Запись результата в trades
**Сделать:**
- при первом заполнении `trades` после entry confirm:
  - вызвать `compute_exit_plan()` и записать поля планировщика в `trades`

**Практический нюанс (P0-допуск):**
- `aggr_flag` зависит от microticks. В live-потоке можно:
  - (минимум P0) писать план сразу; `aggr_flag` будет корректен, когда microticks уже есть в CH;
  - если microticks пишутся позже, `aggr_flag` можно обновлять отдельным snapshot в `controller_state` (append-only), не мутируя `trades`.

**Acceptance:**
- planned_* поля в `trades` не пустые; `glue_select` для trade_id возвращает те же значения при одинаковом состоянии БД.

---

## 6) “Freeze P0”
**Сделать:**
- добавить branch protection / CODEOWNERS на:
  `docs/**, configs/**, schemas/**, queries/**, scripts/**`
- любые изменения проходят только через CI gates (anti-drift/canary/oracle)

**Acceptance:**
- drift не попадает в main

---
