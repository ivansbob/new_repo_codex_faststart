# SPEC — GMEE P0 (v0.4, Variant A)

P0 цель: зафиксировать **контракты + каркас данных/проверок**, чтобы:
- писать must-log с первой сделки,
- симы/прогоны были воспроизводимы,
- **не было drift** между `configs/*.yaml ↔ queries/*.sql ↔ schemas/*.sql ↔ docs/*`.

P0 **не** включает тюнинг, ML, полноценный routing/bandit/ε-контроллер. Только: **contracts + storage + canary + CI gates**.

---

## 1) Единственные источники правды (P0)

- **Числа/пороги:** `configs/golden_exit_engine.yaml`
- **Read API (единственный):** `configs/queries.yaml` + `queries/01..04.sql`
- **Storage DDL:** `schemas/clickhouse.sql`, `schemas/postgres.sql`
- **Контракты:** этот документ + `docs/DATA_MODEL.md` + `docs/CONTRACT_MATRIX.md`

---

## 2) Writer ordering (контракт, P0 hard)

Запись событий обязана быть упорядочена так, чтобы любой `trace_id` можно было восстановить end-to-end:

1) `signals_raw` — входной сигнал (создаётся `trace_id`)
2) `trade_attempts` — **pre-sign** запись attempt (создаётся `attempt_id`, `idempotency_token`, `payload_hash`)
3) `rpc_events` — per-arm ответы/наблюдения (latency/confirm quality)
4) `trades` — 1 строка на lifecycle (entry+exit поля могут быть частично пустыми на момент entry)
5) `microticks_1s` — 1s snapshots только post-entry окно (MVP)

---

## 3) Attempt contract (idempotency / nonce / concurrency)

### 3.1 Attempt (attempt_id) — определение

**Attempt** = одна логическая попытка выполнить `entry` или `exit` для `trade_id`, включая fanout по RPC и сетевые ретраи, **пока payload не изменился**.

### 3.2 Когда создаём новый attempt_id

Новый `attempt_id` создаётся **только если изменилось хотя бы одно**:
- `payload_hash` (фактически другой tx/instructions/signature),
- `nonce_scope` + `nonce_value` (если меняет фактический tx),
- `stage` (`entry` vs `exit`).

Ретраи “отправить тот же payload ещё раз” = **тот же attempt_id** (увеличивается `retry_count`).

### 3.3 Idempotency token

`idempotency_token` = sha256(normalized(payload) + our_wallet + stage + salt)

Внутри одного attempt **не меняется** и служит ключом дедупа fanout/ретраев.

---

## 4) Confirmation policy (confirm_quality)

Мы различаем качество подтверждения, чтобы **не обучаться на мусоре**:

- `ok` — достаточное включение по политике сети/провайдера; можно:
  - считать latency/ε,
  - включать сделку в wallet aggregates (`wallet_daily_agg_state`).

- `suspect` — tx “видна”/наблюдается частично, но inclusion не подтверждено в пределах таймаутов или ответы RPC конфликтуют.
  **Запрещено** использовать для обучения latency/ε и профиля кошелька.

- `reorged` — ранее было `ok`, но позже откат/исчезновение из канонической истории.
  **Запрещено** использовать для обучения latency/ε и профиля.

`entry_first_confirm_time` = первая отметка времени, когда tx стала `ok`.

---

## 5) Forensics events (P0 hard)

`forensics_events` пишется на аномалии, которые ломают доверие к метрикам:

- `time_skew` — нарушена монотонность `signal_time ≤ entry_local_send_time ≤ entry_first_confirm_time`
- `suspect_confirm` — длительный suspect/конфликт подтверждений
- `reorg` — откат подтверждения
- `partial_confirm` — entry ok, exit нет (или наоборот) после SLO
- `schema_mismatch` — missing Tier-0 полей / spikes null-rates

---

## 6) Exit-planner read contract (P0)

P0 планировщик реализуется “как данные/SQL”, без бизнес-кода:

- Профиль кошелька: `queries/01_profile_query.sql`
- Routing state: `queries/02_routing_query.sql`
- Microticks окно: `queries/03_microticks_window.sql`
- Glue/exit plan: `queries/04_glue_select.sql` (Variant A: все числа — параметры)

Выход `04_glue_select.sql` (P0 stable):

- `mode` (U|S|M|L)
- `planned_hold_sec`
- `epsilon_ms` (effective, после pad+clamp)
- `planned_exit_ts`
- `aggr_flag`

---

## 7) Promotion gates (до бизнес-кода)

Пока не пройдены гейты ниже — **запрещено** писать бизнес-код, тюнить или расширять сбор:

1) DDL применился на пустой ClickHouse
2) `EXPLAIN SYNTAX` компилирует `queries/01..04.sql`
3) `scripts/assert_no_drift.py` проходит (Variant A no-hardcode + TTL match + mapping contract)
4) Canary seed+checks проходят
5) Oracle dataset → `04_glue_select.sql` → TSV совпадает с expected (детерминированно)
