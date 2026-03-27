# PR-014 — PORTFOLIO-RISK-SIZING-AND-KILLSWITCH-V1

## Цель
Довести sizing и risk envelope до usable вида.

## Трогать
- repo/strategy/risk_engine.py
- repo/integration/portfolio_stub.py
- repo/docs/risk_envelope.md
- repo/tests/**

## Не трогать
- Не подключать brokerage/live exchange
- Не снимать safety caps
- Не смешивать strategy thresholds и risk caps

## Definition of Done
- Есть position sizing config, caps, kill switch
- Paper учитывает exposure/token/wallet limits

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

Execute only PR-014: PORTFOLIO-RISK-SIZING-AND-KILLSWITCH-V1.

Goal:
Довести sizing и risk envelope до usable вида.

Rules:
- do only this PR
- do not start PR-015
- keep changes minimal and deterministic
- preserve existing repo structure
- return a new zip only

The output zip must include:
- repo/
- PR_NOTES.md
- CHANGED_FILES.md
- TEST_COMMANDS.md
- NEXT_PR_SUGGESTION.md
