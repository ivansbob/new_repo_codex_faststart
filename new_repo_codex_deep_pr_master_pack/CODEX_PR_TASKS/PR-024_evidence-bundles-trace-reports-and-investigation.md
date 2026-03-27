# PR-024 — EVIDENCE-BUNDLES-TRACE-REPORTS-AND-INVESTIGATION

## Цель
Сделать investigation first-class с evidence bundles.

## Трогать
- repo/vendor/**
- repo/tools/**
- repo/scripts/**
- repo/tests/**
- repo/docs/investigation.md

## Не трогать
- Не делать внешние SaaS зависимости
- Не смешивать forensic reports с core writes
- Не ломать trace model

## Definition of Done
- Есть bundle validation, HTML report, investigate flow
- Любой run можно собрать в evidence artifact

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

Execute only PR-024: EVIDENCE-BUNDLES-TRACE-REPORTS-AND-INVESTIGATION.

Goal:
Сделать investigation first-class с evidence bundles.

Rules:
- do only this PR
- do not start PR-025
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
