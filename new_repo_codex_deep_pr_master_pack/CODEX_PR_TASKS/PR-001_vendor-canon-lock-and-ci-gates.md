# PR-001 — VENDOR-CANON-LOCK-AND-CI-GATES

## Цель
Зафиксировать canon/vendor слой как read-only и добавить CI smoke на drift.

## Трогать
- repo/.github/**
- repo/CODEOWNERS
- repo/scripts/canon_smoke.sh
- repo/docs/canon_governance.md

## Не трогать
- Не менять runtime-логику
- Не импортировать новые subsystem-ы
- Не трогать strategy kernel

## Definition of Done
- CI падает при несанкционированном изменении canon/vendor
- Есть governance note как вносить осознанные изменения

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

Execute only PR-001: VENDOR-CANON-LOCK-AND-CI-GATES.

Goal:
Зафиксировать canon/vendor слой как read-only и добавить CI smoke на drift.

Rules:
- do only this PR
- do not start PR-002
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
