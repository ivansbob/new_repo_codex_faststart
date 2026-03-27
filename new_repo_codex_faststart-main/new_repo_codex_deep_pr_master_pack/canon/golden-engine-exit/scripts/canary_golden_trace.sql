-- scripts/canary_golden_trace.sql
-- Inserts a minimal end-to-end golden trace (deterministic IDs/timestamps).
-- Purpose: CI canary + smoke checks for writer ordering and schema compatibility.

-- 1) signals_raw
INSERT INTO signals_raw
  (trace_id, chain, source, signal_id, signal_time, traced_wallet, token_mint, pool_id, confidence, payload_json, ingested_at)
VALUES
  (toUUID('00000000-0000-0000-0000-0000000000a1'), 'solana', 'canary', 'sig_canary_1',
   toDateTime64('2026-01-01 00:00:00.000', 3, 'UTC'),
   'wallet_canary_1', 'token_canary_1', 'pool_canary_1', 0.99, '{"kind":"canary"}',
   toDateTime64('2026-01-01 00:00:00.000', 3, 'UTC'));

-- 2) trade_attempts (pre-sign)
INSERT INTO trade_attempts
  (attempt_id, trade_id, trace_id, chain, env, stage, our_wallet, idempotency_token, payload_hash, attempt_no, retry_count,
   nonce_u64, nonce_scope, nonce_value, local_send_time, rpc_sent_list, client_version, build_sha)
VALUES
  (toUUID('00000000-0000-0000-0000-0000000000b1'),
   toUUID('00000000-0000-0000-0000-0000000000c1'),
   toUUID('00000000-0000-0000-0000-0000000000a1'),
   'solana', 'canary', 'entry', 'our_wallet_canary',
   'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
   'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd',
   1, 0, 0, 'sol_blockhash', 'bh_canary',
   toDateTime64('2026-01-01 00:00:00.050', 3, 'UTC'),
   ['rpc_canary_a'],
   'canary-writer', 'canary-sha');

-- 3) rpc_events (per arm)
INSERT INTO rpc_events
  (attempt_id, trade_id, trace_id, chain, env, stage, idempotency_token, rpc_arm, sent_ts,
   first_seen_ts, first_confirm_ts, finalized_ts, ok_bool, err_code, latency_ms, confirm_quality, tx_sig, block_ref)
VALUES
  (toUUID('00000000-0000-0000-0000-0000000000b1'),
   toUUID('00000000-0000-0000-0000-0000000000c1'),
   toUUID('00000000-0000-0000-0000-0000000000a1'),
   'solana', 'canary', 'entry',
   'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
   'rpc_canary_a',
   toDateTime64('2026-01-01 00:00:00.050', 3, 'UTC'),
   toDateTime64('2026-01-01 00:00:00.060', 3, 'UTC'),
   toDateTime64('2026-01-01 00:00:00.080', 3, 'UTC'),
   NULL,
   1, 'ok', 30, 'ok',
   'tx_canary_1', 'slot_1');

-- 4) trades (lifecycle row)
INSERT INTO trades (
  trade_id, trace_id, experiment_id, config_hash, env, chain, source,
  traced_wallet, our_wallet, token_mint, pool_id,
  signal_time, entry_local_send_time, entry_first_confirm_time, entry_latency_ms, entry_confirm_quality,
  entry_attempt_id, entry_idempotency_token, entry_attempt_no, entry_nonce_u64, entry_nonce_scope, entry_nonce_value,
  entry_rpc_sent_list, entry_rpc_winner, entry_tx_sig,
  buy_time, buy_price_usd, amount_usd,
  mode, planned_hold_sec, epsilon_ms, margin_mult, aggr_flag, planned_exit_ts,
  hold_seconds, roi, success_bool, failure_mode,
  vet_pass, vet_flags, front_run_flag,
  model_version, build_sha
) VALUES (
  toUUID('00000000-0000-0000-0000-0000000000c1'),
  toUUID('00000000-0000-0000-0000-0000000000a1'),
  toUUID('00000000-0000-0000-0000-0000000000d1'),
  'eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee',
  'canary', 'solana', 'canary',
  'wallet_canary_1', 'our_wallet_canary', 'token_canary_1', 'pool_canary_1',
  toDateTime64('2026-01-01 00:00:00.000', 3, 'UTC'),
  toDateTime64('2026-01-01 00:00:00.050', 3, 'UTC'),
  toDateTime64('2026-01-01 00:00:00.080', 3, 'UTC'),
  30, 'ok',
  toUUID('00000000-0000-0000-0000-0000000000b1'),
  'cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc',
  1, 0, 'sol_blockhash', 'bh_canary',
  ['rpc_canary_a'], 'rpc_canary_a', 'tx_canary_1',
  toDateTime64('2026-01-01 00:00:00.000', 3, 'UTC'),
  1.0, 100.0,
  '', 0, 0, 0.0, 0, NULL,
  10, 0.01, 1, 'none',
  1, [], 0,
  'gmee-v0.4', 'canary-sha'
);

-- 5) microticks_1s (post-entry window)
INSERT INTO microticks_1s (trade_id, chain, t_offset_s, ts, price_usd, liquidity_usd, volume_usd) VALUES
  (toUUID('00000000-0000-0000-0000-0000000000c1'), 'solana', 0, toDateTime64('2026-01-01 00:00:00.000', 3, 'UTC'), 1.00, 100000.0, 1000.0);
