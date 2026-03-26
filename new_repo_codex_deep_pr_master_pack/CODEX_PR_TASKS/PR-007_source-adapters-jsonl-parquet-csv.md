# PR-007 — SOURCE-ADAPTERS-JSONL-PARQUET-CSV

## Цель
Добавить универсальные source adapters для offline intake.

## Трогать
- repo/ingestion/**
- repo/integration/trade_normalizer.py
- repo/tests/**

## Не трогать
- Не делать live API ingestion на этом PR
- Не смешивать source parsing и business logic
- Не ломать jsonl path

## Definition of Done
- JSONL/Parquet/CSV поддерживаются единообразно
- Есть smoke загрузка каждого формата

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

Execute only PR-007: SOURCE-ADAPTERS-JSONL-PARQUET-CSV.

Goal:
Добавить универсальные source adapters для offline intake.

Rules:
- do only this PR
- do not start PR-008
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
