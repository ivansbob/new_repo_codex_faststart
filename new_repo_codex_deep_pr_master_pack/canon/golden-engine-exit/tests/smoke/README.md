# Smoke tests (E2E)

Goal: run a minimal pipeline in canary/testnet mode.
- ingest a small set of signals
- generate trades rows (sim/paper)
- verify monotonic time audit, idempotency, and query read-path

Run frequency: scheduled (daily) + on every promotion.
