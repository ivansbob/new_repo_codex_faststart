# PR-018 — IMPORT-PROMOTION-PIPELINE-FROM-MAIN-ENGINE

## Цель
Подключить promotion/runtime loop без live automation.

## Трогать
- repo/promotion/**
- repo/pipeline/**
- repo/tests/**
- repo/docs/promotion_import.md

## Не трогать
- Не включать агрессивный auto-live
- Не дублировать guard logic
- Не ломать replay/paper separation

## Definition of Done
- Есть promotion state machine, cooldowns, guards, rollout reports
- Runtime loop работает в controlled mode

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

Execute only PR-018: IMPORT-PROMOTION-PIPELINE-FROM-MAIN-ENGINE.

Goal:
Подключить promotion/runtime loop без live automation.

Rules:
- do only this PR
- do not start PR-019
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
