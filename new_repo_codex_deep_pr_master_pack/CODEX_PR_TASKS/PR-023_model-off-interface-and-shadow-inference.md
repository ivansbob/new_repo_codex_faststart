# PR-023 — MODEL-OFF-INTERFACE-AND-SHADOW-INFERENCE

## Цель
Подключить model-off и shadow inference без live dependency.

## Трогать
- repo/integration/**
- repo/features/**
- repo/tests/**
- repo/docs/model_off.md

## Не трогать
- Не интегрировать внешнее serving infra
- Не делать auto-apply predictions
- Не ломать deterministic rails

## Definition of Done
- Predictions attached as artifacts
- Shadow inference запускается безопасно

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

Execute only PR-023: MODEL-OFF-INTERFACE-AND-SHADOW-INFERENCE.

Goal:
Подключить model-off и shadow inference без live dependency.

Rules:
- do only this PR
- do not start PR-024
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
