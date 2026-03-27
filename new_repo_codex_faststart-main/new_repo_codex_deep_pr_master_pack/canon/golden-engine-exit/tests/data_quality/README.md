# Data quality checks

Minimum checks:
- null-rate for must-log fields ~= 0 (core)
- monotonic time violations rate
- microticks volume bounded by post-entry window
- latency state freshness
- idempotency dedupe hit-rate (alerts if too high/too low)
