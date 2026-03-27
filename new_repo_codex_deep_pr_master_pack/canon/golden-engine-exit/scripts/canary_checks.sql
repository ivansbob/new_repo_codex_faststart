-- scripts/canary_checks.sql
-- Canary checks that MUST fail CI on contract/schema breakage.
-- Uses throwIf(condition, message) to raise an exception.

-- 1) signals_raw exists (exactly 1)
SELECT throwIf(count() != 1, 'CANARY_FAIL: signals_raw missing or duplicated')
FROM signals_raw
WHERE trace_id = toUUID('00000000-0000-0000-0000-0000000000a1');

-- 2) trade_attempts exists (exactly 1)
SELECT throwIf(count() != 1, 'CANARY_FAIL: trade_attempts missing or duplicated')
FROM trade_attempts
WHERE attempt_id = toUUID('00000000-0000-0000-0000-0000000000b1');

-- 3) rpc_events exists and has ok confirm_quality
SELECT throwIf(countIf(ok_bool = 1 AND confirm_quality = 'ok') != 1, 'CANARY_FAIL: rpc_events missing ok confirm')
FROM rpc_events
WHERE attempt_id = toUUID('00000000-0000-0000-0000-0000000000b1');

-- 4) trades exists and monotonicity holds
SELECT throwIf(
  countIf(NOT (signal_time <= entry_local_send_time AND entry_local_send_time <= entry_first_confirm_time)) > 0,
  'CANARY_FAIL: monotonicity violated (signal_time <= local_send_time <= first_confirm_time)'
)
FROM trades
WHERE trade_id = toUUID('00000000-0000-0000-0000-0000000000c1');

-- 5) microticks exist
SELECT throwIf(count() < 1, 'CANARY_FAIL: microticks_1s missing')
FROM microticks_1s
WHERE trade_id = toUUID('00000000-0000-0000-0000-0000000000c1');

-- 6) MV produced wallet_daily_agg_state row
SELECT throwIf(count() < 1, 'CANARY_FAIL: mv_wallet_daily_agg_state did not populate wallet_daily_agg_state')
FROM wallet_daily_agg_state
WHERE chain = 'solana' AND wallet = 'wallet_canary_1' AND day = toDate('2026-01-01');

-- 7) No critical forensics for this trace
SELECT throwIf(countIf(severity = 'crit') > 0, 'CANARY_FAIL: critical forensics events present')
FROM forensics_events
WHERE trace_id = toUUID('00000000-0000-0000-0000-0000000000a1');
