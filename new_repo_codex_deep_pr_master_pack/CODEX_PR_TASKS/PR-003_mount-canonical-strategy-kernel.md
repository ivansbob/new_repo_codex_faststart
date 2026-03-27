# PR-003 — MOUNT-CANONICAL-STRATEGY-KERNEL

## Цель
Подключить strategy.py как центральный decision kernel.

## Трогать
- repo/core_strategy/**
- repo/integration/**
- repo/docs/strategy_kernel.md

## Не трогать
- Не изобретать новую стратегию
- Не смешивать aggressive layer с entry layer
- Не убирать существующие guards

## Definition of Done
- Есть единый adapter от runtime к CopyScalpStrategy
- Strategy kernel вызывается как canonical decision layer

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

Execute only PR-003: MOUNT-CANONICAL-STRATEGY-KERNEL.

Goal:
Подключить strategy.py как центральный decision kernel.

Rules:
- do only this PR
- do not start PR-004
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
