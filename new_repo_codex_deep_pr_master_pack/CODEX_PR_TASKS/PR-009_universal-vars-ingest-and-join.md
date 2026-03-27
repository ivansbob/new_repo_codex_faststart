# PR-009 — UNIVERSAL-VARS-INGEST-AND-JOIN

## Цель
Подключить UV-путь и joins с provenance.

## Трогать
- repo/features/**
- repo/integration/**
- repo/docs/uv_join_contract.md
- repo/tests/**

## Не трогать
- Не делать тяжёлую фиче-инженерию вне scope
- Не скрывать provenance
- Не дублировать joins в нескольких местах

## Definition of Done
- UV joins работают по time bucket
- Каждое joined поле имеет source_ref/provenance

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

Execute only PR-009: UNIVERSAL-VARS-INGEST-AND-JOIN.

Goal:
Подключить UV-путь и joins с provenance.

Rules:
- do only this PR
- do not start PR-010
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
