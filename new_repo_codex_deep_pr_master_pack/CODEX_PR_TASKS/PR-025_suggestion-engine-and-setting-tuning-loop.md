# PR-025 — SUGGESTION-ENGINE-AND-SETTING-TUNING-LOOP

## Цель
Подключить advisory tuning loop и suggest_settings.

## Трогать
- repo/vendor/**
- repo/integration/**
- repo/tools/**
- repo/tests/**
- repo/docs/suggestion_engine.md

## Не трогать
- Не auto-apply suggestions
- Не менять strategy без artifact trail
- Не скрывать rulepack source

## Definition of Done
- Есть advisory suggestions по settings
- Suggestions сохраняются как artifacts и traceable

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

Execute only PR-025: SUGGESTION-ENGINE-AND-SETTING-TUNING-LOOP.

Goal:
Подключить advisory tuning loop и suggest_settings.

Rules:
- do only this PR
- do not start PR-026
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
