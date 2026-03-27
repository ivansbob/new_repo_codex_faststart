# PR-013 — PAPER-PIPELINE-SOURCE-MODE-RUNNER

## Цель
Сделать paper_pipeline основным runnable режимом.

## Трогать
- repo/integration/paper_pipeline.py
- repo/scripts/**
- repo/docs/paper_runner.md
- repo/tests/**

## Не трогать
- Не строить live runner
- Не ломать deterministic outputs
- Не убирать append-only outputs

## Definition of Done
- Paper запускается из CLI по source mode
- Есть output dirs, manifests, coverage summary

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

Execute only PR-013: PAPER-PIPELINE-SOURCE-MODE-RUNNER.

Goal:
Сделать paper_pipeline основным runnable режимом.

Rules:
- do only this PR
- do not start PR-014
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
