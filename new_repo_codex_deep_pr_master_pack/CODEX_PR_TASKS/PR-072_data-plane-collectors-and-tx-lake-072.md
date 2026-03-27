# PR-072 — DATA-PLANE-COLLECTORS-AND-TX-LAKE-072

## Цель
Расширить collectors, tx lake, evidence capture, snapshots, source provenance, chain ingestion, datagatherers и lake contracts.

## Трогать
- repo/collectors/**
- repo/integration/**
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

Execute only PR-072: DATA-PLANE-COLLECTORS-AND-TX-LAKE-072.

Goal:
Расширить collectors, tx lake, evidence capture, snapshots, source provenance, chain ingestion, datagatherers и lake contracts.

Rules:
- do only this PR
- do not start PR-073
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
