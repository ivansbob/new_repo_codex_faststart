# PR-012 — EXECUTION-PREFLIGHT-HARDENING-ROUTE-SLIPPAGE-LATENCY

## Цель
Расширить execution preflight route/slippage/latency/liquidity sanity.

## Трогать
- repo/integration/execution_preflight.py
- repo/execution/**
- repo/tests/**

## Не трогать
- Не отправлять реальные транзакции
- Не внедрять внешние RPC вызовы
- Не смешивать with promotion logic

## Definition of Done
- Execution preflight выдаёт строгую taxonomy reject'ов
- Есть coverage для route/slippage/latency cases

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

Execute only PR-012: EXECUTION-PREFLIGHT-HARDENING-ROUTE-SLIPPAGE-LATENCY.

Goal:
Расширить execution preflight route/slippage/latency/liquidity sanity.

Rules:
- do only this PR
- do not start PR-013
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
