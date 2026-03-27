# PR-016 — IMPORT-REPLAY-MODULES-FROM-MAIN-ENGINE

## Цель
Импортировать зрелые replay subsystem modules.

## Трогать
- repo/replay/**
- repo/scripts/replay_*
- repo/tests/**
- repo/docs/replay_import.md

## Не трогать
- Не тянуть сразу promotion/trading всё вместе
- Не рефакторить replay под новый стиль
- Не ломать baseline paths

## Definition of Done
- Historical replay harness работает внутри нового repo
- Есть smoke и docs по запуску replay

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

Execute only PR-016: IMPORT-REPLAY-MODULES-FROM-MAIN-ENGINE.

Goal:
Импортировать зрелые replay subsystem modules.

Rules:
- do only this PR
- do not start PR-017
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
