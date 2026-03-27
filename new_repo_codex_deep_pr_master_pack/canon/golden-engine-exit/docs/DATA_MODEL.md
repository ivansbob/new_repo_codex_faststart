# DATA_MODEL — GMEE P0 (v0.4)

Этот документ фиксирует **Tier-0 must-log** контракты данных GMEE, чтобы:
- симы/метрики были воспроизводимы,
- масштабирование 200→1000 кошельков не ломало storage/чтение,
- можно было тюнить позже (P1) без “дыр” в логах.

DDL источник правды: `schemas/clickhouse.sql`
Read API источник правды: `configs/queries.yaml` + `queries/*.sql`

---

## 0) Инварианты (Tier-0, обязательны)

### 0.1 Canonical time (UTC)

Все времена: `DateTime64(3,'UTC')`

Инвариант: `signal_time ≤ entry_local_send_time ≤ entry_first_confirm_time`

Нарушение → `forensics_events(kind='time_skew')`.

### 0.2 IDs / дедуп / идемпотентность

Обязательные идентификаторы:

- `trace_id` — сквозной signal→attempt→rpc→trade→microticks
- `trade_id` — lifecycle сделки
- `attempt_id` — одна попытка (см. SPEC)
- `idempotency_token` — ключ дедупа внутри attempt
- `config_hash`, `experiment_id` — воспроизводимость прогонов

---

## 1) ClickHouse таблицы (P0 ядро)

### 1.1 signals_raw (append-only)

Назначение: сырой входной поток для replay/audit.

TTL: ограниченный retention (см. YAML/DDL).

Must-log: `trace_id, chain, source, signal_id, signal_time, traced_wallet, token_mint, pool_id, confidence, payload_json, ingested_at`

Keys: `PARTITION BY (chain,toYYYYMM(signal_time))`, `ORDER BY (chain,signal_time,source,signal_id)`

### 1.2 trade_attempts (append-only, pre-sign)

Назначение: якорь attempt/idempotency (без него нельзя корректно тюнить/дедупить).

Must-log: `attempt_id, trade_id, trace_id, chain, env, stage, our_wallet, idempotency_token, payload_hash, attempt_no, retry_count, nonce_scope, nonce_value, local_send_time, rpc_sent_list[]`

Tier-1 nullable (по флагу): `tx_size_bytes, dex_route, broadcast_spread_ms, mempool_size_at_send`

Keys: `PARTITION BY (chain,toYYYYMM(local_send_time))`, `ORDER BY (chain,env,stage,our_wallet,local_send_time,attempt_id)`

### 1.3 rpc_events (append-only)

Назначение: latency/ε, bandit priors, circuit breaker, forensics.

Must-log: `attempt_id, trade_id, trace_id, chain, env, stage, idempotency_token, rpc_arm, sent_ts, first_seen_ts?, first_confirm_ts?, finalized_ts?, ok_bool, err_code, latency_ms?, confirm_quality, tx_sig?, block_ref?`

TTL: ограниченный retention.

Keys: `PARTITION BY (chain,toYYYYMM(sent_ts))`, `ORDER BY (chain,rpc_arm,sent_ts,trade_id)`

### 1.4 trades (append-only, 1 row = lifecycle)

Назначение: главный must-log для профилей кошельков и разбора исходов.

Must-log (ядро):

- IDs/dims: `trade_id, trace_id, experiment_id, config_hash, env, chain, source`
- Entities: `traced_wallet, our_wallet, token_mint, pool_id`
- Canonical time: `signal_time, entry_local_send_time, entry_first_confirm_time`
- Routing: `entry_latency_ms, entry_confirm_quality`
- Economics: `buy_time, buy_price_usd, amount_usd`
- GMEE output: `mode, planned_hold_sec, epsilon_ms, margin_mult, aggr_flag, planned_exit_ts`
- Outcome: `hold_seconds, roi, success_bool, failure_mode`
- Risk/vet: `vet_pass, vet_flags[], front_run_flag`
- Audit: `model_version, build_sha, created_at`

Keys: `PARTITION BY (chain,toYYYYMM(buy_time))`, `ORDER BY (env,chain,traced_wallet,buy_time,trade_id)`

Retention: long (TTL отсутствует при `trades_ttl_days=0`).

### 1.5 microticks_1s (append-only, только post-entry окно)

Назначение: детект “убежала быстро” (aggr) и форензика post-entry.

Правило: писать только `t_offset_s ∈ [0..microticks.window_sec]`.

TTL: ограниченный retention.

Keys: `PARTITION BY (chain,toYYYYMM(ts))`, `ORDER BY (chain,trade_id,t_offset_s)`

### 1.6 wallet_daily_agg_state (AggregatingMergeTree)

Назначение: дешёвый профиль кошелька (квантили hold + win/roi).

Источник заполнения: MV `mv_wallet_daily_agg_state` (строгий quality filter).

### 1.7 latency_arm_state (snapshots)

Назначение: runtime читает готовые ε/priors/breaker, без тяжёлых пересчётов.

Must-log: `chain, rpc_arm, snapshot_ts, q90_latency_ms, ewma_mean_ms, ewma_var_ms2, epsilon_ms, a_success, b_success, degraded, cooldown_until?`

### 1.8 controller_state (snapshots)

Назначение: аудит тюнинга/гейтов/промоций конфигов.

Must-log: `chain, key, ts, value_json, config_hash, approved_by?, ticket_ref?`

### 1.9 provider_usage_daily

Назначение: бюджет/квоты провайдеров.

Must-log: `day, provider, chain, calls, errors, cost_usd_est, budget_usd, throttled`

### 1.10 forensics_events

Назначение: централизованный лог аномалий (см. SPEC).

Must-log: `event_id, ts, chain, env, trace_id?, trade_id?, attempt_id?, kind, severity, details_json`

---

## 2) MV/VIEW (P0 ровно минимум)

- MV `mv_wallet_daily_agg_state`: `trades → wallet_daily_agg_state`
  - Quality filter: `success_bool=1 AND failure_mode='none' AND hold_seconds>0 AND entry_confirm_quality='ok'`
- VIEW `wallet_profile_30d`: детерминированный, anchored на `max(day)` в `wallet_daily_agg_state`.

---

## 3) Read API (единственный)

Разрешены только `queries/01..04.sql` (реестр в `configs/queries.yaml`).

Любое новое чтение данных — только через добавление в `configs/queries.yaml` + CI drift-gate.
