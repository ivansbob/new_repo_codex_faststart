# PR-020 — IMPORT-COLLECTORS-WALLETS-AND-SCHEMAS

## Цель
Импортировать collectors, wallet intelligence и schemas.

## Трогать
- repo/collectors/**
- repo/wallets/**
- repo/schemas/**
- repo/tests/**

## Не трогать
- Не тащить всё network-enabled по умолчанию
- Не ломать offline mode
- Не убирать existing baseline schemas

## Definition of Done
- Wallet intelligence layer и collectors доступны
- Schemas синхронизированы и документированы

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

Execute only PR-020: IMPORT-COLLECTORS-WALLETS-AND-SCHEMAS.

Goal:
Импортировать collectors, wallet intelligence и schemas.

Rules:
- do only this PR
- do not start PR-021
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
