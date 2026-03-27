# Idempotency / Reorg / Circuit breaker (операционная обвязка)

## 1) Idempotency (multi-RPC fanout)
Цель: повторный сигнал/ретрай не должен создавать второй trade.

Рекомендуемый ключ:
- `idempotency_key = sha256(chain|wallet_traced|token|pool_id|signal_time_utc|source|experiment_id)`

Политика:
- Дедуп по `idempotency_key` в окне `dedupe_window_sec`.
- Ретраи: максимум N попыток, экспоненциальный backoff.
- Concurrency: сериализация по wallet или по (wallet, token) — чтобы не ловить race на nonce/sequence.

## 2) Partial confirmation / reorg
### Solana
- явная политика `commitment` (processed/confirmed/finalized).
- если подтверждение стало сомнительным → помечаем trade как `failure_mode=reorg_suspect` и карантин.

### EVM
- считаем сделку подтверждённой при N confirmations.
- если reorg в окне → карантин и корректировка PnL/ROI.

## 3) Per-arm circuit breaker
- if `fail_rate > threshold` OR `p90_latency > baseline * mult` → `cooldown_until`
- circuit breaker не должен ломать сим: в симе тоже логируем cooldown и выбор arms.

## 4) Signed artifacts (promotion audit)
- любой canary/promotion должен иметь:
  - run manifest (config_hash, seed, datasets)
  - summary metrics + CI/p-value
  - подпись (GPG/KMS) + запись в `promotion_audit`
