# PR-010 — SIGNAL-ENGINE-V1-GATES-MODES-TIERS

## Цель
Собрать единый signal engine до sim/paper.

## Трогать
- repo/integration/gates.py
- repo/integration/mode_registry.py
- repo/integration/wallet_tier_registry.py
- repo/integration/signal_engine.py
- repo/tests/**

## Не трогать
- Не запускать execution из signal engine
- Не вплетать replay импорт раньше времени
- Не ломать current paper entrypoint

## Definition of Done
- Есть final decision object
- Signal engine агрегирует gates/mode/tier/model-off decision в одном месте

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

Execute only PR-010: SIGNAL-ENGINE-V1-GATES-MODES-TIERS.

Goal:
Собрать единый signal engine до sim/paper.

Rules:
- do only this PR
- do not start PR-011
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
