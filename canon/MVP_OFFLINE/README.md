# MVP_OFFLINE — runnable skeleton

Сквозная цепочка (без RPC/вебхуков/платных сервисов):

`Trade → Signal → Sim entry/exit → PnL/metrics`

## Быстрый старт

1) Установить зависимости:

```bash
python -m pip install -r requirements.txt
```

2) Запустить на CSV‑заглушке:

```bash
python -m src.pipelines.backtest_offline \
  --trades data/processed/trades_stub.csv \
  --config config/params_base.yaml \
  --bankroll 10000
```

## Про конфиг

`config/params_base.yaml` — **тот же** файл, что и в корне pack (`/config/params_base.yaml`) — единый источник правды.

MVP_OFFLINE читает этот YAML и делает **нормализацию** в компактные секции (`wallet_gates/token_gates/modes/risk/execution`),
чтобы текущие модули симуляции работали и на “богатом” конфиге v3.0.

## Входной контракт

Смотри `INPUT_CONTRACT.md` (CSV или Parquet).


## Unified Decision Formula
Этот MVP содержит упрощённый pipeline. Каноническая спецификация принятия решения находится в:
- `../UNIFIED_DECISION_FORMULA_ONE_FORMULA.md`
- конфиг‑параметры в `../config/params_base.yaml` (блок `decision_formula`).
