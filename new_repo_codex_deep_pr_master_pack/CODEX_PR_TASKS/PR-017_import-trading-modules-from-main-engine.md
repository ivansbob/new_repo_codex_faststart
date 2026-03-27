# PR-017 — IMPORT-TRADING-MODULES-FROM-MAIN-ENGINE

## Цель
Импортировать зрелый trading subsystem.

## Трогать
- repo/trading/**
- repo/tests/**
- repo/docs/trading_import.md

## Не трогать
- Не включать live auto-trading
- Не ломать paper path
- Не переписывать fills/friction без причины

## Definition of Done
- Position/PnL/fill/friction модули доступны в новом repo
- Paper может использовать mature trading helpers

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

Execute only PR-017: IMPORT-TRADING-MODULES-FROM-MAIN-ENGINE.

Goal:
Импортировать зрелый trading subsystem.

Rules:
- do only this PR
- do not start PR-018
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
