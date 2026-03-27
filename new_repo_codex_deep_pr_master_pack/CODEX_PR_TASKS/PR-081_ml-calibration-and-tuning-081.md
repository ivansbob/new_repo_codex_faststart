# PR-081 — ML-CALIBRATION-AND-TUNING-081

## Цель
Развить calibration, shadow models, feature selection, leaderboard/reporting, config suggestion loops, analyzer slices, experiment manifests.

## Трогать
- repo/features/**
- repo/analytics/**
- repo/tools/**
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

Execute only PR-081: ML-CALIBRATION-AND-TUNING-081.

Goal:
Развить calibration, shadow models, feature selection, leaderboard/reporting, config suggestion loops, analyzer slices, experiment manifests.

Rules:
- do only this PR
- do not start PR-082
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
