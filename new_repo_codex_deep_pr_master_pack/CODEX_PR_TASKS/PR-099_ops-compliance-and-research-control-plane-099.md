# PR-099 — OPS-COMPLIANCE-AND-RESEARCH-CONTROL-PLANE-099

## Цель
Усилить smoke/canary/doctor, evidence exports, runbooks, privacy/compliance, ZipWiz operator cockpit, pack builders, handoff automation.

## Трогать
- repo/scripts/**
- repo/docs/**
- control_plane/zipwiz/**
- repo/tests/**

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

Execute only PR-099: OPS-COMPLIANCE-AND-RESEARCH-CONTROL-PLANE-099.

Goal:
Усилить smoke/canary/doctor, evidence exports, runbooks, privacy/compliance, ZipWiz operator cockpit, pack builders, handoff automation.

Rules:
- do only this PR
- do not start PR-100
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
