# PR-019 — IMPORT-ANALYTICS-AND-SCORING-FROM-MAIN-ENGINE

## Цель
Подключить analytics/scoring/unified score.

## Трогать
- repo/analytics/**
- repo/scoring/**
- repo/tests/**
- repo/docs/scoring_import.md

## Не трогать
- Не обучать модели в этом PR
- Не дублировать score formulas
- Не смешивать analyzer reports с runtime writes

## Definition of Done
- Unified score и analyzer доступны как subsystem
- Есть smoke по score pipeline

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

Execute only PR-019: IMPORT-ANALYTICS-AND-SCORING-FROM-MAIN-ENGINE.

Goal:
Подключить analytics/scoring/unified score.

Rules:
- do only this PR
- do not start PR-020
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
