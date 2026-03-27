# PROBATION

Trigger (examples):
- sim_success below gate
- sustained slippage increase
- time_skew events
- repeated circuit-breaker activation

Actions:
- Pause wallet (or wallet group).
- Run enhanced sim (seeded, N>=500) on last window.
- Decide: rollback config, adjust epsilon/margin, or exclude provider.
