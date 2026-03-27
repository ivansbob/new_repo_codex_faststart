# PR-008 — ALLOWLIST-WALLET-PROFILES-TOKEN-SNAPSHOTS-V1

## Цель
Усилить stores allowlist / wallet profiles / token snapshots.

## Трогать
- repo/integration/*store*.py
- repo/integration/allowlist_loader.py
- repo/tests/**

## Не трогать
- Не переносить ещё main-engine wallets
- Не добавлять network fetches
- Не менять strategy kernel

## Definition of Done
- Stores versioned и покрыты fixture tests
- paper/sim могут стабильно читать snapshot/profile данные

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

Execute only PR-008: ALLOWLIST-WALLET-PROFILES-TOKEN-SNAPSHOTS-V1.

Goal:
Усилить stores allowlist / wallet profiles / token snapshots.

Rules:
- do only this PR
- do not start PR-009
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
