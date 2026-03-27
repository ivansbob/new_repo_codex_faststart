-- queries/01_profile_query.sql
-- Read API: returns 30d profile for one traced wallet.
SELECT
  chain, wallet, trades_n, win_rate,
  q10_hold_sec, q25_hold_sec, q40_hold_sec, median_hold_sec,
  avg_hold_sec, hold_var_sec2, avg_roi, roi_var
FROM wallet_profile_30d
WHERE chain = {chain:String} AND wallet = {wallet:String};
