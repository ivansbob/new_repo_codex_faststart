-- queries/04_glue_select.sql
-- Read API: glue profile + routing + microticks -> exit plan (P0 stable output).
-- Variant A (P0 hard): ALL thresholds/epsilon/aggr/clamp are placeholders (NO hardcoded numbers from YAML).

WITH
  {chain:String} AS p_chain,
  {trade_id:UUID} AS p_trade_id,

  {min_hold_sec:UInt32} AS p_min_hold_sec,
  {mode_u_max_sec:UInt32} AS p_mode_u_max_sec,
  {mode_s_max_sec:UInt32} AS p_mode_s_max_sec,
  {mode_m_max_sec:UInt32} AS p_mode_m_max_sec,

  {margin_mult:Float32} AS p_margin_mult,
  {max_hold_sec:UInt32} AS p_max_hold_sec,

  {epsilon_pad_ms:UInt32} AS p_epsilon_pad_ms,
  {epsilon_min_ms:UInt32} AS p_epsilon_min_ms,
  {epsilon_max_ms:UInt32} AS p_epsilon_max_ms,

  {aggr_u_up_pct:Float32} AS p_aggr_u_up_pct,
  {aggr_s_up_pct:Float32} AS p_aggr_s_up_pct,
  {aggr_m_up_pct:Float32} AS p_aggr_m_up_pct,
  {aggr_l_up_pct:Float32} AS p_aggr_l_up_pct,

  {aggr_u_window_s:UInt16} AS p_aggr_u_window_s,
  {aggr_s_window_s:UInt16} AS p_aggr_s_window_s,
  {aggr_m_window_s:UInt16} AS p_aggr_m_window_s,
  {aggr_l_window_s:UInt16} AS p_aggr_l_window_s,

  {microticks_window_s:UInt16} AS p_microticks_window_s

SELECT mode, planned_hold_sec, epsilon_ms, planned_exit_ts, aggr_flag
FROM (
  WITH
    -- deterministic anchor for routing state
    (SELECT max(snapshot_ts) FROM latency_arm_state WHERE chain = p_chain) AS routing_anchor_ts,

    -- routing epsilon: choose smallest epsilon among non-degraded arms not in cooldown at anchor
    (
      WITH per_arm AS (
        SELECT
          rpc_arm,
          argMax(epsilon_ms, snapshot_ts) AS epsilon_ms,
          argMax(degraded, snapshot_ts) AS degraded,
          argMax(cooldown_until, snapshot_ts) AS cooldown_until
        FROM latency_arm_state
        WHERE chain = p_chain AND snapshot_ts <= routing_anchor_ts
        GROUP BY rpc_arm
      )
      SELECT ifNull(
        minIf(
          epsilon_ms,
          (degraded = 0) AND (isNull(cooldown_until) OR cooldown_until <= routing_anchor_ts)
        ),
        0
      )
      FROM per_arm
    ) AS routing_epsilon_ms,

    -- effective epsilon: pad + clamp
    least(
      greatest(routing_epsilon_ms + p_epsilon_pad_ms, p_epsilon_min_ms),
      p_epsilon_max_ms
    ) AS effective_epsilon_ms

  SELECT
    base.mode AS mode,
    base.planned_hold_sec AS planned_hold_sec,
    toUInt32(effective_epsilon_ms) AS epsilon_ms,
    (base.buy_time + toIntervalSecond(base.planned_hold_sec) - toIntervalMillisecond(toUInt64(effective_epsilon_ms))) AS planned_exit_ts,
    base.aggr_flag AS aggr_flag
  FROM (
    SELECT
      t.trade_id,
      t.buy_time,
      t.traced_wallet,

      -- wallet profile (defaults if missing)
      ifNull(wp.avg_hold_sec, 0.0) AS avg_hold_sec,
      ifNull(wp.q10_hold_sec, 0.0) AS q10_hold_sec,
      ifNull(wp.q25_hold_sec, 0.0) AS q25_hold_sec,
      ifNull(wp.q40_hold_sec, 0.0) AS q40_hold_sec,
      ifNull(wp.median_hold_sec, 0.0) AS median_hold_sec,

      -- mode selection by avg_hold_sec
      multiIf(
        avg_hold_sec <= toFloat64(p_mode_u_max_sec), 'U',
        avg_hold_sec <= toFloat64(p_mode_s_max_sec), 'S',
        avg_hold_sec <= toFloat64(p_mode_m_max_sec), 'M',
        'L'
      ) AS mode,

      -- quantile mapping contract:
      -- U -> q10_hold_sec, S -> q25_hold_sec, M -> q40_hold_sec, L -> median_hold_sec
      multiIf(
        mode = 'U', q10_hold_sec,
        mode = 'S', q25_hold_sec,
        mode = 'M', q40_hold_sec,
        median_hold_sec
      ) AS base_hold_sec,

      -- planned hold = clamp(round(base_hold_sec * margin_mult), min..max)
      toUInt32(
        least(
          greatest(round(base_hold_sec * toFloat64(p_margin_mult)), toFloat64(p_min_hold_sec)),
          toFloat64(p_max_hold_sec)
        )
      ) AS planned_hold_sec,

      -- microticks-based aggr flag (“убежала быстро”) using per-mode params
      (
        WITH mt AS (
          SELECT
            trade_id,
            argMin(price_usd, t_offset_s) AS p0,
            argMaxIf(price_usd, t_offset_s, t_offset_s <= p_aggr_u_window_s) AS p_u,
            argMaxIf(price_usd, t_offset_s, t_offset_s <= p_aggr_s_window_s) AS p_s,
            argMaxIf(price_usd, t_offset_s, t_offset_s <= p_aggr_m_window_s) AS p_m,
            argMaxIf(price_usd, t_offset_s, t_offset_s <= p_aggr_l_window_s) AS p_l
          FROM microticks_1s
          WHERE chain = p_chain AND trade_id = p_trade_id AND t_offset_s <= p_microticks_window_s
          GROUP BY trade_id
        )
        SELECT toUInt8(
          (p0 > 0) AND (
            (
              (multiIf(mode = 'U', p_u, mode = 'S', p_s, mode = 'M', p_m, p_l) / p0) - 1
            ) >= toFloat64(
              multiIf(mode = 'U', p_aggr_u_up_pct, mode = 'S', p_aggr_s_up_pct, mode = 'M', p_aggr_m_up_pct, p_aggr_l_up_pct)
            )
          )
        )
        FROM mt
      ) AS aggr_flag

    FROM trades t
    LEFT JOIN wallet_profile_30d wp ON wp.chain = t.chain AND wp.wallet = t.traced_wallet
    WHERE t.chain = p_chain AND t.trade_id = p_trade_id
    LIMIT 1
  ) AS base
) AS out;
