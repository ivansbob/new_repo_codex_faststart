# STOP_ALL

Trigger examples:
- Massive RPC failures / time skew spike
- Budget overrun that risks outages
- Detected reorg storm / confirmation instability

Actions (MVP):
1) Pause trading path (paper/live) via flag.
2) Keep must-log and diagnostic capture enabled.
3) Start incident log with `config_hash`, `experiment_id`, time window.
