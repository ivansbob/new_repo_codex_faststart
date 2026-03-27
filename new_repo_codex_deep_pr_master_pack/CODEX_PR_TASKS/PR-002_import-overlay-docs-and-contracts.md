# PR-002 — IMPORT-OVERLAY-DOCS-AND-CONTRACTS

## Цель
Перенести docs/spec/contracts слой из overlay в новый repo.

## Трогать
- canon/**
- repo/docs/**
- repo/schemas/**
- repo/templates/**

## Не трогать
- Не переписывать документы своим стилем
- Не добавлять runtime-код поверх docs
- Не ломать пути из baseline

## Definition of Done
- В repo лежат event/contracts/templates/docs как canonical reference
- Есть README что откуда импортировано

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

Execute only PR-002: IMPORT-OVERLAY-DOCS-AND-CONTRACTS.

Goal:
Перенести docs/spec/contracts слой из overlay в новый repo.

Rules:
- do only this PR
- do not start PR-003
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
