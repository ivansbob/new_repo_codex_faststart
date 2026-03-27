# CI smoke (P0)

Цель: чтобы любые правки в `docs/SPEC.md`, `docs/DATA_MODEL.md`, `schemas/*.sql`, `queries/01..04.sql` не ломали “1:1 freeze” тихо.

## 1) Минимальный smoke для ClickHouse

1) Поднять ClickHouse (локально/docker/CI)
2) Прогнать DDL из `schemas/clickhouse.sql`
3) Запустить компиляцию 4 канонических запросов `queries/01..04.sql` с тестовыми параметрами.

Готовый скрипт: `scripts/ch_smoke.sh`.

Пример:

```bash
# defaults: localhost:9000 user=default
./scripts/ch_smoke.sh

# с параметрами
(removed)=127.0.0.1 CLICKHOUSE_PORT=9000 CLICKHOUSE_USER=default ./scripts/ch_smoke.sh
```

## 2) "Локальная" проверка 1:1

Ручное правило P0:

- любое поле, которое упоминается в `docs/SPEC.md`, должно существовать в `docs/DATA_MODEL.md` и в DDL
- все таблицы/ключи из `docs/DATA_MODEL.md` должны существовать в `schemas/clickhouse.sql` / `schemas/postgres.sql`
- `queries/01..04.sql` — единственный источник runtime-чтения (версионируется в репо)

## 3) Дополнительно (после появления данных)

- ежедневный `docs/QA_DAILY.md` как job
- запись summary в `gmee.forensics_events(kind='schema_mismatch'|...)`


Note: This repo's local smoke uses `docker compose exec clickhouse ...` (host env vars are not used).
