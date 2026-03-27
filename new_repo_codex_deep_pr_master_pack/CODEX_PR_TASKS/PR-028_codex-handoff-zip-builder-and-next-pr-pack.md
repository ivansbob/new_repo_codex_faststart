# PR-028 — CODEX-HANDOFF-ZIP-BUILDER-AND-NEXT-PR-PACK

## Цель
Формализовать вечный цикл handoff zip -> next PR zip.

## Трогать
- repo/tools/**
- repo/scripts/**
- repo/docs/codex_handoff.md
- repo/tests/**

## Не трогать
- Не паковать мусор/временные артефакты
- Не ломать repo layout
- Не делать multi-PR in one pack

## Definition of Done
- Есть builder для следующего Codex zip
- После любого PR можно собрать clean next-step pack

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

Execute only PR-028: CODEX-HANDOFF-ZIP-BUILDER-AND-NEXT-PR-PACK.

Goal:
Формализовать вечный цикл handoff zip -> next PR zip.

Rules:
- do only this PR
- do not start PR-029
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
