# PR-006 — WRITER-ORDERING-AND-FORENSICS-CONTRACT

## Цель
Зацементировать порядок append-only записи и trace forensics.

## Трогать
- repo/integration/write_*
- repo/integration/run_trace.py
- repo/docs/forensics_contract.md
- repo/tests/**

## Не трогать
- Не менять business logic принятия сигнала
- Не удалять существующие event writers
- Не ломать trace_id

## Definition of Done
- Есть deterministic ordering contract
- Каждая запись связана trace/run ids и расследуема

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

Execute only PR-006: WRITER-ORDERING-AND-FORENSICS-CONTRACT.

Goal:
Зацементировать порядок append-only записи и trace forensics.

Rules:
- do only this PR
- do not start PR-007
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
