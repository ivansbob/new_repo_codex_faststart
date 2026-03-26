# GMEE — Golden Mean Exit Engine (P0 skeleton, v0.4)

Это **каркас P0**: **contracts + storage + canary + CI gates**.  
Цель P0 — сделать так, чтобы Codex/автогенерация писали бизнес-код **без догадок** и без дрейфа между **YAML ↔ SQL ↔ DDL ↔ docs**.

## Ключевое решение (P0 hard)

**Variant A**: в `queries/04_glue_select.sql` **все** пороги/epsilon/aggr/clamp/окна — **только параметры** `{name:Type}`.

CI валит билд, если:
- параметры в `configs/queries.yaml` не совпадают 1:1 с плейсхолдерами в SQL,
- в `04_glue_select.sql` есть захардкоженные литералы равные значениям из YAML,
- отсутствует контракт маппинга `U->q10, S->q25, M->q40, L->median`,
- DDL (TTL) не совпадает с YAML,
- canary/oracle тесты не проходят.

## Структура репозитория

- `docs/` — канон контрактов (SPEC/DATA_MODEL/CONTRACT_MATRIX/RUNBOOK)
- `configs/` — единственные источники чисел/порогов и read-API registry
- `schemas/` — DDL (ClickHouse/Postgres)
- `queries/` — канонические SQL read-API
- `scripts/` — canary/oracle seeds + anti-drift gate
- `.github/workflows/` — CI gate (ClickHouse smoke)

## Локальный smoke (аналог CI)

Нужен ClickHouse (например `clickhouse/clickhouse-server:24.3`) и Python3.

```bash
# 1) DDL
clickhouse-client --multiquery < schemas/clickhouse.sql

# 2) Anti-drift
python3 scripts/assert_no_drift.py

# 3) Canary
clickhouse-client --multiquery < scripts/canary_golden_trace.sql
clickhouse-client --multiquery < scripts/canary_checks.sql

# 4) Oracle (seed + glue_select)
clickhouse-client --multiquery < scripts/seed_golden_dataset.sql

# Пример запуска 04_glue_select.sql (параметры берите из configs/golden_exit_engine.yaml):
clickhouse-client --format=TSVRaw   --param_chain=solana   --param_trade_id=00000000-0000-0000-0000-000000000011   --param_min_hold_sec=5   --param_mode_u_max_sec=35   --param_mode_s_max_sec=130   --param_mode_m_max_sec=220   --param_margin_mult=1   --param_max_hold_sec=900   --param_epsilon_pad_ms=150   --param_epsilon_min_ms=10   --param_epsilon_max_ms=2000   --param_aggr_u_up_pct=0.03   --param_aggr_s_up_pct=0.06   --param_aggr_m_up_pct=0.10   --param_aggr_l_up_pct=0.15   --param_aggr_u_window_s=12   --param_aggr_s_window_s=30   --param_aggr_m_window_s=60   --param_aggr_l_window_s=90   --param_microticks_window_s=120   < queries/04_glue_select.sql
```

## P0 Done-Definition (DoD)

P0 считается закрытым, если:
- `schemas/clickhouse.sql` применим на пустой БД,
- `EXPLAIN SYNTAX` компилирует `queries/01..04.sql`,
- `scripts/assert_no_drift.py` проходит (нет drift),
- canary seed + checks проходят,
- oracle seed + сравнение TSV результата `04_glue_select.sql` проходит в CI.

## Один Codex-prompt (скопируй и используй как единственный)

**Задача:** писать бизнес-код ТОЛЬКО поверх контрактов P0. Никаких новых схем/порогов “на глаз”.

**PROMPT**
1. Прочитай: `docs/CONTRACT_MATRIX.md`, затем `docs/SPEC.md`, затем `docs/DATA_MODEL.md`.
2. Единственные источники чисел — `configs/golden_exit_engine.yaml`.
3. Единственный read-API — `configs/queries.yaml` + `queries/*.sql`.
4. Любые пороги/epsilon/aggr/clamp/окна в planner должны приходить параметрами в `queries/04_glue_select.sql` (Variant A).
5. Запрещено хардкодить значения из YAML в SQL/коде; если нужно число — добавь его в YAML и прокинь параметром (и обнови CONTRACT_MATRIX + анти-дрейф).
6. Писать логи строго по writer ordering: `signals_raw → trade_attempts → rpc_events → trades → microticks_1s`.
7. Заполнять поля планировщика в `trades` **только** из результата `queries/04_glue_select.sql` (mode/planned_hold_sec/epsilon_ms/planned_exit_ts/aggr_flag).
8. Любое изменение, которое ломает CI gates (anti-drift / canary / oracle) — запрещено. Сначала поправь контракты/гейты.

## Local smoke helpers

To run the same gates locally that CI runs (schema + drift + compile + canary + oracle):

```bash
./scripts/ch_smoke.sh
```

To print the oracle output for `queries/04_glue_select.sql` (TSVRaw) after seeding:

```bash
python3 scripts/run_oracle_glue_select.py --chain solana --trade-id 00000000-0000-0000-0000-000000000011
```
