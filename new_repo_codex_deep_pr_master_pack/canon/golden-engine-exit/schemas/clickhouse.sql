-- schemas/clickhouse.sql
-- GMEE P0 storage schema (v0.4) — Variant A
-- Must be applicable on an empty ClickHouse database.

-- 0) signals_raw (append-only)
CREATE TABLE IF NOT EXISTS signals_raw (
  trace_id UUID,
  chain LowCardinality(String),
  source LowCardinality(String),
  signal_id String,
  signal_time DateTime64(3,'UTC'),
  traced_wallet String,
  token_mint String,
  pool_id String,
  confidence Nullable(Float32),
  payload_json String,
  ingested_at DateTime64(3,'UTC') DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY (chain, toYYYYMM(signal_time))
ORDER BY (chain, signal_time, source, signal_id)
TTL signal_time + toIntervalDay(180) DELETE;

-- 1) trade_attempts (append-only, pre-sign / idempotency anchor)
CREATE TABLE IF NOT EXISTS trade_attempts (
  attempt_id UUID,
  trade_id UUID,
  trace_id UUID,
  chain LowCardinality(String),
  env LowCardinality(String),            -- sim|paper|live|canary|testnet
  stage LowCardinality(String),          -- entry|exit
  our_wallet String,
  idempotency_token FixedString(64),
  payload_hash FixedString(64),
  attempt_no UInt16,
  retry_count UInt16,
  nonce_u64 UInt64,                      -- EVM nonce; 0 if N/A
  nonce_scope LowCardinality(String),    -- sol_blockhash|evm_nonce|other
  nonce_value Nullable(String),          -- e.g. Solana recentBlockhash
  local_send_time DateTime64(3,'UTC'),
  rpc_sent_list Array(LowCardinality(String)),

  -- Tier-1 optional (nullable)
  tx_size_bytes Nullable(UInt32),
  dex_route Nullable(String),
  broadcast_spread_ms Nullable(UInt32),
  mempool_size_at_send Nullable(UInt32),

  client_version LowCardinality(String),
  build_sha LowCardinality(String),
  created_at DateTime64(3,'UTC') DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY (chain, toYYYYMM(local_send_time))
ORDER BY (chain, env, stage, our_wallet, local_send_time, attempt_id);

-- 2) rpc_events (append-only, per-RPC-arm telemetry)
CREATE TABLE IF NOT EXISTS rpc_events (
  attempt_id UUID,
  trade_id UUID,
  trace_id UUID,
  chain LowCardinality(String),
  env LowCardinality(String),
  stage LowCardinality(String),          -- entry|exit
  idempotency_token FixedString(64),
  rpc_arm LowCardinality(String),
  sent_ts DateTime64(3,'UTC'),
  first_seen_ts Nullable(DateTime64(3,'UTC')),
  first_confirm_ts Nullable(DateTime64(3,'UTC')),
  finalized_ts Nullable(DateTime64(3,'UTC')),
  ok_bool UInt8,
  err_code LowCardinality(String),
  latency_ms Nullable(UInt32),
  confirm_quality LowCardinality(String), -- ok|suspect|reorged
  tx_sig Nullable(String),
  block_ref Nullable(String),
  created_at DateTime64(3,'UTC') DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY (chain, toYYYYMM(sent_ts))
ORDER BY (chain, rpc_arm, sent_ts, trade_id)
TTL sent_ts + toIntervalDay(90) DELETE;

-- 3) trades (append-only, 1 row = lifecycle)
CREATE TABLE IF NOT EXISTS trades (
  -- IDs / dims
  trade_id UUID,
  trace_id UUID,
  experiment_id UUID,
  config_hash FixedString(64),
  env LowCardinality(String),
  chain LowCardinality(String),
  source LowCardinality(String),

  -- Entities
  traced_wallet String,
  our_wallet String,
  token_mint String,
  pool_id String,

  -- Canonical time chain
  signal_time DateTime64(3,'UTC'),
  entry_local_send_time DateTime64(3,'UTC'),
  entry_first_confirm_time DateTime64(3,'UTC'),
  entry_latency_ms UInt32,
  entry_confirm_quality LowCardinality(String), -- ok|suspect|reorged

  -- Entry attempt linkage
  entry_attempt_id UUID,
  entry_idempotency_token FixedString(64),
  entry_attempt_no UInt16,
  entry_nonce_u64 UInt64,
  entry_nonce_scope LowCardinality(String),
  entry_nonce_value Nullable(String),
  entry_rpc_sent_list Array(LowCardinality(String)),
  entry_rpc_winner LowCardinality(String),
  entry_tx_sig Nullable(String),

  -- Economics
  buy_time DateTime64(3,'UTC'),
  buy_price_usd Float64,
  amount_usd Float64,
  liquidity_at_entry_usd Nullable(Float64),
  fee_paid_entry_usd Nullable(Float32),

  -- GMEE output (planner)
  mode LowCardinality(String),  -- U|S|M|L
  planned_hold_sec UInt32,
  epsilon_ms UInt32,
  margin_mult Float32,
  aggr_flag UInt8,
  planned_exit_ts Nullable(DateTime64(3,'UTC')),

  -- Exit (optional)
  exit_attempt_id Nullable(UUID),
  exit_idempotency_token Nullable(FixedString(64)),
  exit_nonce_u64 Nullable(UInt64),
  exit_nonce_scope Nullable(LowCardinality(String)),
  exit_nonce_value Nullable(String),
  exit_rpc_sent_list Array(LowCardinality(String)),
  exit_rpc_winner LowCardinality(String),
  exit_tx_sig Nullable(String),
  exit_local_send_time Nullable(DateTime64(3,'UTC')),
  exit_first_confirm_time Nullable(DateTime64(3,'UTC')),
  exit_confirm_quality LowCardinality(String),
  fee_paid_exit_usd Nullable(Float32),
  sell_time Nullable(DateTime64(3,'UTC')),
  sell_price_usd Nullable(Float64),

  -- Outcome
  hold_seconds UInt32,
  roi Float32,
  slippage_pct Nullable(Float32),
  success_bool UInt8,
  failure_mode LowCardinality(String), -- none|rpc_error|latency_timeout|slippage_exceed|mev|rug|reorg|time_skew|data_bad|unknown

  -- Risk/vet
  vet_pass UInt8,
  vet_flags Array(LowCardinality(String)),
  mev_risk_prob Nullable(Float32),
  front_run_flag UInt8,

  -- Tier-1 optional (nullable)
  tx_size_bytes Nullable(UInt32),
  dex_route Nullable(String),
  broadcast_spread_ms Nullable(UInt32),
  mempool_size_at_send Nullable(UInt32),

  -- Audit
  model_version LowCardinality(String),
  build_sha LowCardinality(String),
  created_at DateTime64(3,'UTC') DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY (chain, toYYYYMM(buy_time))
ORDER BY (env, chain, traced_wallet, buy_time, trade_id);

-- 4) microticks_1s (post-entry window only)
CREATE TABLE IF NOT EXISTS microticks_1s (
  trade_id UUID,
  chain LowCardinality(String),
  t_offset_s UInt16,
  ts DateTime64(3,'UTC'),
  price_usd Float64,
  liquidity_usd Nullable(Float64),
  volume_usd Nullable(Float64)
)
ENGINE = MergeTree
PARTITION BY (chain, toYYYYMM(ts))
ORDER BY (chain, trade_id, t_offset_s)
TTL ts + toIntervalDay(60) DELETE;

-- 5) wallet_daily_agg_state (AggregatingMergeTree)
CREATE TABLE IF NOT EXISTS wallet_daily_agg_state (
  chain LowCardinality(String),
  wallet String,
  day Date,
  trades_state AggregateFunction(count),
  wins_state AggregateFunction(sum, UInt8),
  hold_q_state AggregateFunction(quantilesTDigest(0.10,0.25,0.40,0.50), Float64),
  hold_avg_state AggregateFunction(avg, Float64),
  hold_var_state AggregateFunction(varPop, Float64),
  roi_avg_state AggregateFunction(avg, Float32),
  roi_var_state AggregateFunction(varPop, Float32)
)
ENGINE = AggregatingMergeTree
PARTITION BY (chain, toYYYYMM(day))
ORDER BY (chain, wallet, day);

-- 6) latency_arm_state (snapshots, append-only)
CREATE TABLE IF NOT EXISTS latency_arm_state (
  chain LowCardinality(String),
  rpc_arm LowCardinality(String),
  snapshot_ts DateTime64(3,'UTC'),
  q90_latency_ms UInt32,
  ewma_mean_ms Float32,
  ewma_var_ms2 Float32,
  epsilon_ms UInt32,
  a_success Float32,
  b_success Float32,
  degraded UInt8,
  cooldown_until Nullable(DateTime64(3,'UTC')),
  meta_json String DEFAULT ''
)
ENGINE = MergeTree
PARTITION BY (chain, toYYYYMM(snapshot_ts))
ORDER BY (chain, snapshot_ts, rpc_arm);

-- 7) controller_state (snapshots, append-only)
CREATE TABLE IF NOT EXISTS controller_state (
  chain LowCardinality(String),
  key LowCardinality(String),
  ts DateTime64(3,'UTC'),
  value_json String,
  config_hash FixedString(64),
  approved_by Nullable(String),
  ticket_ref Nullable(String)
)
ENGINE = MergeTree
PARTITION BY (chain, toYYYYMM(ts))
ORDER BY (chain, key, ts);

-- 8) provider_usage_daily (budget / quota)
CREATE TABLE IF NOT EXISTS provider_usage_daily (
  day Date,
  provider LowCardinality(String),
  chain LowCardinality(String),
  calls UInt64,
  errors UInt64,
  cost_usd_est Float64,
  budget_usd Float64,
  throttled UInt8,
  created_at DateTime64(3,'UTC') DEFAULT now64(3)
)
ENGINE = MergeTree
PARTITION BY toYYYYMM(day)
ORDER BY (provider, chain, day);

-- 9) forensics_events (append-only)
CREATE TABLE IF NOT EXISTS forensics_events (
  event_id UUID,
  ts DateTime64(3,'UTC') DEFAULT now64(3),
  chain LowCardinality(String),
  env LowCardinality(String),
  trace_id Nullable(UUID),
  trade_id Nullable(UUID),
  attempt_id Nullable(UUID),
  kind LowCardinality(String),      -- time_skew|reorg|partial_confirm|suspect_confirm|schema_mismatch|other
  severity LowCardinality(String),  -- info|warn|crit
  details_json String
)
ENGINE = MergeTree
PARTITION BY (chain, toYYYYMM(ts))
ORDER BY (chain, ts, kind, severity);

-- ---------------------------
-- P0 MV / VIEW (exactly two)
-- ---------------------------

-- MV: trades -> wallet_daily_agg_state
CREATE MATERIALIZED VIEW IF NOT EXISTS mv_wallet_daily_agg_state
TO wallet_daily_agg_state AS
SELECT
  chain,
  traced_wallet AS wallet,
  toDate(buy_time) AS day,
  countState() AS trades_state,
  sumState(toUInt8(roi > 0)) AS wins_state,
  quantilesTDigestState(0.10, 0.25, 0.40, 0.50)(toFloat64(hold_seconds)) AS hold_q_state,
  avgState(toFloat64(hold_seconds)) AS hold_avg_state,
  varPopState(toFloat64(hold_seconds)) AS hold_var_state,
  avgState(toFloat32(roi)) AS roi_avg_state,
  varPopState(toFloat32(roi)) AS roi_var_state
FROM trades
WHERE success_bool = 1 AND failure_mode = 'none' AND hold_seconds > 0 AND entry_confirm_quality = 'ok'
GROUP BY chain, wallet, day;

-- VIEW: wallet_profile_30d (deterministic, anchored on max(day))
CREATE VIEW IF NOT EXISTS wallet_profile_30d AS
WITH
  ifNull((SELECT max(day) FROM wallet_daily_agg_state), toDate('1970-01-01')) AS anchor_day,
  addDays(anchor_day, -30) AS from_day
SELECT
  chain,
  wallet,
  countMerge(trades_state) AS trades_n,
  ifNull(toFloat64(sumMerge(wins_state)) / nullIf(toFloat64(countMerge(trades_state)), 0.0), 0.0) AS win_rate,
  quantilesTDigestMerge(0.10,0.25,0.40,0.50)(hold_q_state) AS hold_qs,
  arrayElement(hold_qs, 1) AS q10_hold_sec,
  arrayElement(hold_qs, 2) AS q25_hold_sec,
  arrayElement(hold_qs, 3) AS q40_hold_sec,
  arrayElement(hold_qs, 4) AS median_hold_sec,
  avgMerge(hold_avg_state) AS avg_hold_sec,
  varPopMerge(hold_var_state) AS hold_var_sec2,
  avgMerge(roi_avg_state) AS avg_roi,
  varPopMerge(roi_var_state) AS roi_var
FROM wallet_daily_agg_state
WHERE day > from_day AND day <= anchor_day
GROUP BY chain, wallet;
