# PR-011 — SIM-PREFLIGHT-HARDENING-NEGATIVE-AND-GROUP-METRICS

## Цель
Сделать sim_preflight обязательным и богаче по отчётности.

## Трогать
- repo/integration/sim_preflight.py
- repo/tests/**
- repo/docs/sim_preflight_contract.md

## Не трогать
- Не добавлять live trading
- Не подменять risk layer
- Не убирать существующие reject reasons

## Definition of Done
- Есть negative and group metrics
- sim_preflight объясняет почему вход запрещён

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

Execute only PR-011: SIM-PREFLIGHT-HARDENING-NEGATIVE-AND-GROUP-METRICS.

Goal:
Сделать sim_preflight обязательным и богаче по отчётности.

Rules:
- do only this PR
- do not start PR-012
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
