-- scripts/seed_golden_dataset.sql
-- Deterministic tiny dataset for oracle test of queries/04_glue_select.sql.
--
-- Oracle expected (TSV) when running queries/04_glue_select.sql with YAML params + trade_id below:
--   U\t20\t250\t2026-01-01 00:00:19.750\t1

-- Base time (kept within TTL windows)
WITH toDateTime64('2026-01-01 00:00:00.000', 3, 'UTC') AS base_ts

-- 1) Routing snapshots (deterministic epsilon choice: rpc_oracle_a wins)
INSERT INTO latency_arm_state (chain, rpc_arm, snapshot_ts, q90_latency_ms, ewma_mean_ms, ewma_var_ms2, epsilon_ms, a_success, b_success, degraded, cooldown_until, meta_json)
VALUES
  ('solana','rpc_oracle_a', base_ts, 120, 100.0, 25.0, 100, 10.0, 1.0, 0, NULL, '{"oracle":true}'),
  ('solana','rpc_oracle_b', base_ts, 300, 250.0, 64.0, 500, 10.0, 1.0, 1, toDateTime64('2027-01-01 00:00:00.000', 3, 'UTC'), '{"oracle":true}');

-- 2) Ten successful trades for wallet_oracle_1 with identical hold_seconds=20 (stable quantiles/avg).
--    The oracle trade_id is the first row below (number=0): ...0011
INSERT INTO trades (
  trade_id, trace_id, experiment_id, config_hash, env, chain, source,
  traced_wallet, our_wallet, token_mint, pool_id,
  signal_time, entry_local_send_time, entry_first_confirm_time, entry_latency_ms, entry_confirm_quality,
  entry_attempt_id, entry_idempotency_token, entry_attempt_no, entry_nonce_u64, entry_nonce_scope, entry_nonce_value,
  entry_rpc_sent_list, entry_rpc_winner, entry_tx_sig,
  buy_time, buy_price_usd, amount_usd,
  hold_seconds, roi, success_bool, failure_mode,
  vet_pass, vet_flags, front_run_flag,
  model_version, build_sha
)
SELECT
  toUUID(concat('00000000-0000-0000-0000-0000000000', lpad(lower(hex(number + 17)), 2, '0'))) AS trade_id,
  toUUID('00000000-0000-0000-0000-000000000111') AS trace_id,
  toUUID('00000000-0000-0000-0000-000000000211') AS experiment_id,
  'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa' AS config_hash,
  'sim' AS env,
  'solana' AS chain,
  'oracle' AS source,
  'wallet_oracle_1' AS traced_wallet,
  'our_wallet_oracle' AS our_wallet,
  'token_oracle' AS token_mint,
  'pool_oracle' AS pool_id,
  addSeconds(base_ts, toInt32(number)) AS signal_time,
  addMilliseconds(addSeconds(base_ts, toInt32(number)), 50) AS entry_local_send_time,
  addMilliseconds(addSeconds(base_ts, toInt32(number)), 100) AS entry_first_confirm_time,
  50 AS entry_latency_ms,
  'ok' AS entry_confirm_quality,
  toUUID(concat('00000000-0000-0000-0000-0000000003', lpad(lower(hex(number + 17)), 2, '0'))) AS entry_attempt_id,
  'bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb' AS entry_idempotency_token,
  1 AS entry_attempt_no,
  0 AS entry_nonce_u64,
  'sol_blockhash' AS entry_nonce_scope,
  'bh_oracle' AS entry_nonce_value,
  ['rpc_oracle_a'] AS entry_rpc_sent_list,
  'rpc_oracle_a' AS entry_rpc_winner,
  concat('tx_oracle_', lpad(toString(number+1), 2, '0')) AS entry_tx_sig,
  addSeconds(base_ts, toInt32(number)) AS buy_time,
  1.0 AS buy_price_usd,
  100.0 AS amount_usd,
  20 AS hold_seconds,
  0.01 AS roi,
  1 AS success_bool,
  'none' AS failure_mode,
  1 AS vet_pass,
  [] AS vet_flags,
  0 AS front_run_flag,
  'gmee-v0.4' AS model_version,
  'oracle' AS build_sha
FROM numbers(10);

-- 3) Microticks for the oracle trade: +4% within 10s -> should trigger aggr for mode U (with YAML params)
INSERT INTO microticks_1s (trade_id, chain, t_offset_s, ts, price_usd, liquidity_usd, volume_usd)
VALUES
  (toUUID('00000000-0000-0000-0000-000000000011'), 'solana', 0,  toDateTime64('2026-01-01 00:00:00.000', 3, 'UTC'), 1.00, 100000.0, 1000.0),
  (toUUID('00000000-0000-0000-0000-000000000011'), 'solana', 10, toDateTime64('2026-01-01 00:00:10.000', 3, 'UTC'), 1.04, 100000.0, 2000.0);
