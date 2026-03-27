# PR-056 — WALLET-INTEL-GRAPH-LINKAGE-056

## Цель
Развить wallet graph, family metadata, linkage scorer, smart-wallet registry, cluster evidence и graph-backed risk features.

## Трогать
- repo/wallets/**
- repo/analytics/**
- repo/tests/**
- repo/docs/**

## Не трогать
- не менять уже принятый canon без явной нужды
- не объединять несколько PR в один
- не ломать deterministic outputs
- не включать live auto-execution
- не удалять существующие smoke/forensics rails

## Definition of Done
- изменения ограничены логикой этого семейства
- есть PR_NOTES.md, CHANGED_FILES.md, TEST_COMMANDS.md, NEXT_PR_SUGGESTION.md
- новый zip готов как handoff для следующего шага
- нет unrelated refactor
- есть хотя бы smoke/fixture coverage для новых изменений

## Короткий prompt для Codex
Use the attached repo zip as the working baseline.

Execute only PR-056: WALLET-INTEL-GRAPH-LINKAGE-056.

Goal:
Развить wallet graph, family metadata, linkage scorer, smart-wallet registry, cluster evidence и graph-backed risk features.

Rules:
- do only this PR
- do not start PR-057
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
