# GMEE Strategy Pack — Index (for Codex)

Этот файл — «оглавление» пакета. Цель: чтобы Codex мог быстро найти (а вы — сослаться) на единственные источники правды.

## Быстрый старт
1) Прочитать стратегию целиком:
- `docs/strategy_all_in_one_v11_1.md`

2) Посмотреть, чем управляется GM Exit Engine:
- `config/golden_mean_exit_engine.yaml`
- `config/params_base.yaml`
- `config/modes.yaml`

3) Понять контракты данных:
- `docs/canonical_field_dictionary.md` (**канонические поля, единицы, алиасы**)
- `docs/gm_min_data_and_event_schema.md` (таблицы + event schema)

## Данные / БД / MVs
- Индексы/partition keys: `docs/gm_storage_keys_and_indexes.md`
- Read-запросы: `docs/gm_read_queries_min.md`
- Обновление `wallet_hold_stats`: `docs/wallet_hold_stats_update_rules.md` и `docs/gm_read_queries_and_wallet_hold_stats_update.md`
- ClickHouse MVs:
  - SQL: `docs/gm_clickhouse_mvs_min.sql`
  - Пояснения: `docs/gm_indices_partitions_and_mvs.md`

## Готовые DDL
- ClickHouse (4 таблицы: trades_raw/positions_reconstructed/wallet_hold_stats/gm_exit_decisions):
  - `schemas/clickhouse/00_tables.sql`
  - `schemas/clickhouse/01_trades_raw.sql`
  - `schemas/clickhouse/02_positions_reconstructed.sql`
  - `schemas/clickhouse/03_wallet_hold_stats.sql`
  - `schemas/clickhouse/04_gm_exit_decisions.sql`
  - MVs: `schemas/clickhouse/10_materialized_views.sql`
- ClickHouse (альт. минимальный pipeline): `schemas/clickhouse/20_alt_min_mvp.sql`
- Postgres: `schemas/postgres/00_tables.sql`, `schemas/postgres/01_tables.sql`

## MVP Offline (быстрый backtest/paper-скелет)
- `MVP_OFFLINE/README.md`
- `MVP_OFFLINE/INPUT_CONTRACT.md`
- `MVP_OFFLINE/src/` (types/strategy/simulator)

## Ключевые документы стратегии
- `UNIFIED_DECISION_FORMULA_ONE_FORMULA.md`
- `SOLANA_COPY_SCALPING_STRATEGY_KERNEL_v1.md`
- `SOLANA_COPY_SCALPING_SPEC_v0_2.md`
- `AGGRESSIVE_LAYER_ROCKET_MODE.md`
- `FREE_FIRST_MONEY_FILTER_AND_PARALLEL_TRACKS.md`
- `STRATEGY_TO_UV_MAPPING.md`

## Инженерия/интеграция
- `ENGINEERING_BLUEPRINT_REPO_AND_MVP_V0.md`
- `GMEE_INTEGRATION_NOTES.md`

## Манифест
- `strategy_manifest.json`
