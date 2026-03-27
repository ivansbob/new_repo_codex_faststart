# TODO (P0 only) — GMEE v0.4 (Variant A)

Этот порядок = “P0 → Codex пишет бизнес-код”.
Пока пункты ниже не закрыты — **не делаем P1/P2** (тюнинг/роутинг/bandit/ε-контроллер/бизнес-код).

## P0-1 Anti-drift (Variant A)

- [ ] `docs/CONTRACT_MATRIX.md` содержит:
  - YAML sources: `configs/golden_exit_engine.yaml`, `configs/queries.yaml`
  - Variant A rules (SQL04 только параметры)
  - CI gates (DDL+EXPLAIN+no_drift+canary+oracle)
- [ ] `scripts/assert_no_drift.py`:
  - placeholders↔queries.yaml params (1:1)
  - запрет hardcoded порогов в `queries/04_glue_select.sql`
  - проверка quantile mapping контракта U/S/M/L
  - DDL↔YAML TTL match
- [ ] CI workflow `.github/workflows/ch_compile_smoke.yml` проходит

## P0-2 Storage (ClickHouse)

- [ ] `schemas/clickhouse.sql` содержит весь P0-набор таблиц:
  - `signals_raw`
  - `trade_attempts`
  - `rpc_events`
  - `trades`
  - `microticks_1s`
  - `wallet_daily_agg_state`
  - `latency_arm_state`
  - `controller_state`
  - `provider_usage_daily`
  - `forensics_events`
- [ ] TTL/retention:
  - signals_raw TTL
  - rpc_events TTL
  - microticks_1s TTL
  - trades: long retention (TTL отсутствует при trades_ttl_days=0)
- [ ] Ровно 2 агрегата:
  - MV `mv_wallet_daily_agg_state`
  - VIEW `wallet_profile_30d` (детерминированный)

## P0-3 Canary + Oracle

- [ ] `scripts/canary_golden_trace.sql` (writer ordering seed)
- [ ] `scripts/canary_checks.sql` (throwIf-checks)
- [ ] `scripts/seed_golden_dataset.sql` (детерминированный tiny dataset)
- [ ] CI сравнивает TSV-выход `queries/04_glue_select.sql` с expected

## P0-4 Spec contracts (Writer / Attempt / Confirm / Forensics)

- [ ] `docs/SPEC.md` фиксирует:
  - writer ordering: `signals_raw → trade_attempts → rpc_events → trades → microticks_1s`
  - attempt_id: новый attempt только при смене payload_hash/nonce_scope+nonce_value/stage
  - confirm_quality: `ok|suspect|reorged` и запрет обучения на `suspect/reorged`
  - forensics_events триггеры

## После P0 (не сейчас)

- [ ] P1: latency→ε job, bandit routing, probation/rollback, cost/quota watcher
- [ ] P2: мультичейн-ингесторы (EVM), Tier-1/2 расширения, risk/MEV модули
