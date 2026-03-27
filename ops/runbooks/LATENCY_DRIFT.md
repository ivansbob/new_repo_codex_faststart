# LATENCY_DRIFT

Trigger:
- p90 latency or epsilon_sec rises above baseline by multiplier, sustained.

Actions:
- Move worst arm(s) to cooldown (circuit breaker).
- Increase epsilon pad or reduce fanout concurrency.
- Re-run canary sim on last 24h data with updated epsilon.
