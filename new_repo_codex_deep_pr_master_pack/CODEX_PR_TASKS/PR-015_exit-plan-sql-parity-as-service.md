# PR-015 — EXIT-PLAN-SQL-PARITY-AS-SERVICE

## Цель
Выделить compute_exit_plan как стабильный service слой с parity.

## Трогать
- repo/vendor/**
- repo/integration/**
- repo/docs/exit_plan_service.md
- repo/tests/**

## Не трогать
- Не размазывать exit SQL по runtime-коду
- Не допускать free-form queries
- Не ломать oracle parity

## Definition of Done
- Есть persisted exit-plan artifact
- 1:1 parity tests проходят

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

Execute only PR-015: EXIT-PLAN-SQL-PARITY-AS-SERVICE.

Goal:
Выделить compute_exit_plan как стабильный service слой с parity.

Rules:
- do only this PR
- do not start PR-016
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
