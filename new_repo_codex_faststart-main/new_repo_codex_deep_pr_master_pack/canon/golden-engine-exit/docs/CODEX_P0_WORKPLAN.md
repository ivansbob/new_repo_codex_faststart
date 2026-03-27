# Codex P0 Workplan — GMEE (Golden Mean Exit Engine)

Этот файл — **пошаговый план для Codex/команды**, чтобы быстро дойти до состояния:
- схемы БД подняты,
- канонические queries работают,
- writer пишет must-log с корректными ID,
- canary/smoke + QA daily ловят поломки,
- можно начинать бизнес-код (planner/exec/sim) без потери воспроизводимости.

## 0) Sources of truth
- **Spec**: `docs/SPEC.md`
- **Data contracts**: `docs/DATA_MODEL.md`
- **DDL**: `schemas/clickhouse.sql`, `schemas/postgres.sql`
- **Query-contracts**: `queries/01..04_*.sql`

---
## 1) Close P0 data contracts (must be first)
### 1.1 Attempt/confirm contract (docs only)
**Deliverable**: в `docs/idempotency_reorg_circuit_breaker.md` и/или `docs/SPEC.md` зафиксированы:
- что такое `attempt` (когда создаём новый `attempt_id`),
- что такое `confirm_quality` (`ok|suspect|reorged`) и как это влияет на обучение ε/квантилей,
- когда пишем `forensics_events`.

**DoD**: любой разработчик может по тексту понять, какой event куда писать.

### 1.2 ClickHouse DDL (schemas/clickhouse.sql)
**Apply** (в порядке):
- `gmee.signals_raw`
- `gmee.trade_attempts` *(P0 add)*
- `gmee.rpc_events`
- `gmee.trades`
- `gmee.microticks_1s`
- `gmee.wallet_daily_agg_state` + `mv_wallet_daily_agg_state` + `wallet_profile_30d`
- `gmee.latency_arm_state`, `gmee.controller_state`
- `gmee.provider_usage_daily`
- `gmee.forensics_events` *(P0 add)*

**DoD**: DDL выполняется без ошибок на чистой БД; VIEW `wallet_profile_30d` возвращает 0 строк (но компилируется).

### 1.3 Postgres DDL (schemas/postgres.sql)
**Apply**:
- `configs` (hash + YAML)
- `experiment_registry`
- `promotions_audit`

**DoD**: вставка `configs` и `experiment_registry` проходит, `config_hash` используется как FK.

---
## 2) Canonical SQL files are the read-API
Codex должен считать, что runtime читает только через эти файлы:
- `queries/01_profile_query.sql` → wallet_profile (30d)
- `queries/02_routing_query.sql` → ε/priors/breaker per arm
- `queries/03_microticks_window.sql` → 1s окно post-entry
- `queries/04_glue_select.sql` → (signals + profile + routing) → параметры планировщика

**DoD**: запросы выполняются на минимальном stub dataset и возвращают ожидаемые колонки.

---
## 3) Writer (single point of truth)
### 3.1 IDs & invariants
Writer обязан генерировать/проставлять:
- `trace_id`, `trade_id`, `attempt_id`
- `idempotency_token`, `experiment_id`, `config_hash`

И обеспечивать инварианты:
- `signal_time <= entry_local_send_time <= entry_first_confirm_time`

### 3.2 What writer writes
Минимальный поток записей (P0):
1) `signals_raw` (при приёме сигнала)
2) `trade_attempts` (до broadcast: nonce/payload_hash/rpc_sent_list)
3) `rpc_events` (на каждый arm)
4) `trades` (после завершения lifecycle либо по timeout с `failure_mode`)
5) `microticks_1s` (только post-entry окно)
6) `forensics_events` (time_skew / suspect / reorg / partial_confirm / schema_mismatch)

**DoD**: по одному `trace_id` можно склеить всю цепочку в аналитике.

---
## 4) Canary E2E smoke + QA daily
### 4.1 Canary/testnet smoke
**Goal**: ежедневно/на каждый деплой прогонять простой trace:
- ingest mock signal → attempt → rpc_events (можно mocked confirm) → trades row.

**DoD**: smoke-trace пишет полный набор Tier‑0 полей, и QA job не ругается.

### 4.2 QA daily
Автоматические проверки:
- monotonicity (time chain)
- null-rate core Tier‑0 полей (trades/trade_attempts/rpc_events)
- drift по `entry_latency_ms`, `success_bool`, `roi` (KS/ADWIN)
- алерт если >1% trades/day без core полей

---
## 5) Controller loops (skeleton)
### 5.1 Latency snapshots job
Пишет `latency_arm_state` (q90 + EWMA var → ε) и breaker flags.

### 5.2 Bandit warmup
Хранит priors `a_success/b_success` в `latency_arm_state` или `controller_state`.

**DoD**: `02_routing_query.sql` всегда возвращает свежий snapshot на `as_of_ts`.

---
## 6) Promotions audit (paper → live)
Любая промоция:
- записывает запись в `promotions_audit` (GO/NO_GO/ROLLBACK)
- прикладывает signed snapshot URI
- указывает связанный `experiment_id`

**DoD**: можно восстановить, *кто* и *почему* продвинул конфиг.
