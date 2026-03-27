# PR-033 — REPLAY-DEEPENING-033

## Цель
Углубить replay truth-layer, deterministic state, backfill resiliency, unresolved trade diagnostics, provider abstractions, replay economic sanity.

## Трогать
- repo/replay/**
- repo/scripts/**
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

Execute only PR-033: REPLAY-DEEPENING-033.

Goal:
Углубить replay truth-layer, deterministic state, backfill resiliency, unresolved trade diagnostics, provider abstractions, replay economic sanity.

Rules:
- do only this PR
- do not start PR-034
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
