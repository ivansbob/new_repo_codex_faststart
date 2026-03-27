# Canary → Promotion

Checklist:
- Canary scope defined (1–5% wallets).
- Registry record exists: config_hash + seed + artifacts.
- Signed summary present.
- No red alerts (latency drift / MEV spike / budget overrun) during window.

Promotion:
- Write `promotion_audit` row with actor and notes.
