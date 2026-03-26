# PR-004 — DB-MIGRATIONS-CLICKHOUSE-POSTGRES

## Цель
Сделать нормальные миграции вместо raw sql.

## Трогать
- repo/db/**
- repo/scripts/db_*
- repo/docs/db_bootstrap.md

## Не трогать
- Не внедрять ORM переписывание
- Не менять schema semantics без причины
- Не ломать существующие sql артефакты

## Definition of Done
- DB поднимается с нуля командами из TEST_COMMANDS
- Есть smoke на пустой БД

## Выход от Codex
- вернуть новый zip
- внутри:
  - repo/
  - PR_NOTES.md
  - CHANGED_FILES.md
  - TEST_COMMANDS.md
  - NEXT_PR_SUGGESTION.md

## Жёсткие правила
- делать только этот PR
- не начинать следующий PR
- не делать unrelated refactor
- минимальные, детерминированные изменения
- сохранить совместимость с уже существующей структурой repo

## Короткий prompt для Codex
Use the attached repo zip as the working baseline.

Execute only PR-004: DB-MIGRATIONS-CLICKHOUSE-POSTGRES.

Goal:
Сделать нормальные миграции вместо raw sql.

Rules:
- do only this PR
- do not start PR-005
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
