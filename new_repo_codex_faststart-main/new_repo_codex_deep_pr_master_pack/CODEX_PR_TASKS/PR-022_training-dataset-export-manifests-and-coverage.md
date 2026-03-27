# PR-022 — TRAINING-DATASET-EXPORT-MANIFESTS-AND-COVERAGE

## Цель
Дожать reproducible export datasets.

## Трогать
- repo/tools/export_training_dataset.py
- repo/scripts/**
- repo/tests/**
- repo/docs/dataset_export.md

## Не трогать
- Не делать model training
- Не экспортировать без manifest/hash
- Не терять coverage artifacts

## Definition of Done
- Parquet/CSV export reproducible
- Есть manifest, config hash, coverage artifacts

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

Execute only PR-022: TRAINING-DATASET-EXPORT-MANIFESTS-AND-COVERAGE.

Goal:
Дожать reproducible export datasets.

Rules:
- do only this PR
- do not start PR-023
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
