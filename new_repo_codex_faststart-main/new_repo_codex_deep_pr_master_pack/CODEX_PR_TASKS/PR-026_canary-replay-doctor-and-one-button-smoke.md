# PR-026 — CANARY-REPLAY-DOCTOR-AND-ONE-BUTTON-SMOKE

## Цель
Довести DX/ops до handoff-ready состояния.

## Трогать
- repo/scripts/**
- repo/tests/**
- repo/docs/doctor_and_smoke.md

## Не трогать
- Не строить новую CI систему с нуля
- Не ломать старые smoke paths
- Не смешивать ops commands с business logic

## Definition of Done
- Есть doctor command, one-button smoke, acceptance summary
- Repo легко проверить с нуля

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

Execute only PR-026: CANARY-REPLAY-DOCTOR-AND-ONE-BUTTON-SMOKE.

Goal:
Довести DX/ops до handoff-ready состояния.

Rules:
- do only this PR
- do not start PR-027
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
