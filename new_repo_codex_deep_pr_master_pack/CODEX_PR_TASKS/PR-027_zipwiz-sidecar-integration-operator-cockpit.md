# PR-027 — ZIPWIZ-SIDECAR-INTEGRATION-OPERATOR-COCKPIT

## Цель
Подключить ZipWiz как отдельный control-plane sidecar.

## Трогать
- control_plane/zipwiz/**
- repo/docs/zipwiz_sidecar.md

## Не трогать
- Не смешивать ZipWiz с execution core
- Не подключать скрытый data collection
- Не ломать privacy/compliance notes

## Definition of Done
- ZipWiz живёт отдельным sidecar слоем
- Есть operator/research hooks и governance docs

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

Execute only PR-027: ZIPWIZ-SIDECAR-INTEGRATION-OPERATOR-COCKPIT.

Goal:
Подключить ZipWiz как отдельный control-plane sidecar.

Rules:
- do only this PR
- do not start PR-028
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
