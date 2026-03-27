# Tuning workflow (без ML)

Цель: тюнить GMEE через конфиги и воспроизводимые симы.

## Что обновлять до данных
- схемы/контракты must-log
- registry + config hashing + artifacts
- idempotency/nonce/circuit breaker
- canary/smoke pipeline

## Что тюнить после первых данных
- `epsilon_k`, `pad_sec`
- thresholds probation
- `margin_start/margin_min`, режимные пороги U/S/M/L (если нужно)
- аггр пороги и действия при `aggr_hit`

## Рекомендуемый цикл
- daily/nightly: обновление wallet_agg (rolling 30d)
- streaming/минутно: latency state snapshots
- weekly: пересмотр порогов probation и бюджета
