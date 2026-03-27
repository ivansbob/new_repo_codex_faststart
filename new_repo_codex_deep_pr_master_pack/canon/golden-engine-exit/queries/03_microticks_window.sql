-- queries/03_microticks_window.sql
-- Read API: returns microticks_1s for a trade in [0..window_s] post-entry window.
SELECT
  trade_id, chain, t_offset_s, ts, price_usd, liquidity_usd, volume_usd
FROM microticks_1s
WHERE chain = {chain:String}
  AND trade_id = {trade_id:UUID}
  AND t_offset_s <= {window_s:UInt16}
ORDER BY t_offset_s ASC;
