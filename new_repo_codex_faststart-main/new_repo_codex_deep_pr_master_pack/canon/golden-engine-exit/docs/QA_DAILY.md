# QA daily (P0)

Минимальный набор ежедневных проверок качества данных GMEE.

Рекомендация: запускать 1× в день (UTC) и писать итог (summary) в `gmee.forensics_events` + алерт.

## 1) Monotonic time chain

Инвариант (P0 минимум):

- `signal_time <= entry_local_send_time <= entry_first_confirm_time`

Проверка (нарушения за 24h):

```sql
SELECT
  chain,
  env,
  count() AS n,
  sum(
    (entry_local_send_time < signal_time)
    OR (entry_first_confirm_time < entry_local_send_time)
  ) AS bad_n,
  bad_n / n AS bad_pct
FROM gmee.trades
WHERE buy_time >= (now('UTC') - INTERVAL 1 DAY)
GROUP BY chain, env
ORDER BY bad_pct DESC;
```

При `bad_pct > 0.001` — алерт и запись в `gmee.forensics_events(kind='time_skew')`.

## 2) Null-rate по Tier-0 полям

Проверка (24h):

```sql
SELECT
  chain,
  env,
  count() AS n,
  sum(traced_wallet = '' OR our_wallet = '' OR token_mint = '' OR pool_id = '') AS bad_identity,
  sum(entry_idempotency_token = '' OR entry_rpc_winner = '' OR entry_latency_ms = 0) AS bad_entry_core,
  sum(mode = '' OR planned_hold_sec = 0 OR epsilon_ms = 0) AS bad_plan_core
FROM gmee.trades
WHERE buy_time >= (now('UTC') - INTERVAL 1 DAY)
GROUP BY chain, env
ORDER BY (bad_identity + bad_entry_core + bad_plan_core) DESC;
```

Если суммарно > 1% (`(bad_identity+bad_entry_core+bad_plan_core)/n > 0.01`) — это `schema_mismatch`.

## 3) Confirm-quality и reorg/suspect

Доля suspect/reorged (24h):

```sql
SELECT
  chain,
  env,
  count() AS n,
  sum(entry_confirm_quality IN ('suspect','reorged')) AS bad_n,
  bad_n / n AS bad_pct
FROM gmee.trades
WHERE buy_time >= (now('UTC') - INTERVAL 1 DAY)
GROUP BY chain, env
ORDER BY bad_pct DESC;
```

Важно: `entry_confirm_quality != 'ok'` не используем для обучения ε/квантилей.

## 4) Сдвиг latency (p90) по сравнению со вчера

Простейший “сигнал тревоги”: сравнить p90 за последние 24h с предыдущими 24h.

```sql
WITH
  now_w AS (
    SELECT chain, quantileExact(0.90)(entry_latency_ms) AS p90_now
    FROM gmee.trades
    WHERE buy_time >= (now('UTC') - INTERVAL 1 DAY)
    GROUP BY chain
  ),
  prev_w AS (
    SELECT chain, quantileExact(0.90)(entry_latency_ms) AS p90_prev
    FROM gmee.trades
    WHERE buy_time < (now('UTC') - INTERVAL 1 DAY)
      AND buy_time >= (now('UTC') - INTERVAL 2 DAY)
    GROUP BY chain
  )
SELECT
  n.chain,
  n.p90_now,
  p.p90_prev,
  if(p.p90_prev = 0, 0, n.p90_now / p.p90_prev) AS ratio
FROM now_w n
LEFT JOIN prev_w p USING chain
ORDER BY ratio DESC;
```

Если `ratio > 1.5` — алерт и запись в `gmee.forensics_events(kind='suspect_confirm'| 'other')` с деталями.
