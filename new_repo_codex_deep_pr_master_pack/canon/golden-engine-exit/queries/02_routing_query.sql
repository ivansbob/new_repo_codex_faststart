-- queries/02_routing_query.sql
-- Read API: returns latest routing/epsilon state per RPC arm (anchored on max(snapshot_ts)).
WITH
  {chain:String} AS p_chain,
  (SELECT max(snapshot_ts) FROM latency_arm_state WHERE chain = p_chain) AS anchor_ts
SELECT
  p_chain AS chain,
  rpc_arm,
  argMax(epsilon_ms, snapshot_ts) AS epsilon_ms,
  argMax(degraded, snapshot_ts) AS degraded,
  argMax(cooldown_until, snapshot_ts) AS cooldown_until,
  argMax(a_success, snapshot_ts) AS a_success,
  argMax(b_success, snapshot_ts) AS b_success,
  anchor_ts AS anchor_ts
FROM latency_arm_state
WHERE chain = p_chain AND snapshot_ts <= anchor_ts
GROUP BY rpc_arm
ORDER BY degraded ASC, epsilon_ms ASC, rpc_arm ASC;
