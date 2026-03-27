# PR-021 — TRADE-FEATURES-V1-WITH-UV-AND-SNAPSHOT-JOINS

## Цель
Собрать полноценный feature builder с joins.

## Трогать
- repo/features/**
- repo/tests/**
- repo/docs/trade_features_v1.md

## Не трогать
- Не обучать модели
- Не скрывать missingness
- Не пропускать provenance на joined полях

## Definition of Done
- Feature matrix строится с coverage report
- Есть labels v1 и joins к snapshots/UV/profiles

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

Execute only PR-021: TRADE-FEATURES-V1-WITH-UV-AND-SNAPSHOT-JOINS.

Goal:
Собрать полноценный feature builder с joins.

Rules:
- do only this PR
- do not start PR-022
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
