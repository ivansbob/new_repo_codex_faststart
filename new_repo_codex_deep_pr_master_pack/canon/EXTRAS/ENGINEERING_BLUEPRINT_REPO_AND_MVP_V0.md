# Engineering Blueprint — боевой репозиторий + раскладка модулей + план MVP v0 (0$)

См. также: `FREE_FIRST_MONEY_FILTER_AND_PARALLEL_TRACKS.md` (free ≥ 7 дней, лимиты, параллельные треки).
Этот документ фиксирует **инженерное ТЗ/blueprint уровня “можно нанимать команду”** для реализации copy‑scalping бота поверх стратегии из `SOLANA_COPY_SCALPING_SPEC_v0_2.md`.

Цель: дать Codex/инженерам **понятную структуру репозитория**, единые **контракты типов/данных** и минимальный **сквозной путь**: *on‑chain event → сигнал → симуляция входа/выхода → PnL*.

---

## 1) Предлагаемая структура боевого репозитория

> Название условное: `solana-copy-scalper/` (Python, легко портируется).

```text
solana-copy-scalper/
  config/
    config.yaml              # параметры: RPC/DEX/риск/режимы/пороги
    modes.yaml               # режимы U/S/M/L + aggressive профили
  data/
    raw/                     # CSV/Parquet выгрузки (Dune/Birdeye/Dexscreener)
    processed/               # нормализованные trades/features/labels
  src/
    __init__.py

    core/
      types.py               # общие dataclass: Trade, WalletProfile, TokenState, Signal, Position
      constants.py           # константы/enum’ы

    ingestion/
      dune_fetch.py          # fetch_top_wallets()
      helius_listener.py     # monitor_wallets_realtime()
      dex_price_feeds.py     # Jupiter/Raydium/Birdeye quotes + liquidity snapshots

    features/
      wallet_profile.py      # build/update WalletProfile + tiering/кластеризация
      token_features.py      # ликвидность/объёмы/волатильность/honeypot
      trade_features.py      # build_features(trade, wallet_profile, token_state)

    models/
      train_xgboost.py       # обучение/сохранение артефакта модели
      predict.py             # predict_success(features) -> (p_model, edge)
      survival.py            # survival analysis для hold_sec / exit_hazard (опционально)

    strategy/
      mode_selector.py       # choose_scalp_mode() + конфиги U/S/M/L
      risk_engine.py         # Kelly/лимиты/kill-switch
      exits.py               # TP/SL, partial TP, trailing stop
      honeypot_filter.py     # is_honeypot_safe()

    execution/
      simulator.py           # simulate_fill_limit_ttl(), simulate_exit()
      queues.py              # queue_parallel_trades(), Redis или in-memory
      live_executor_stub.py  # заглушка live-исполнения (пока только лог/сим)

    monitoring/
      metrics.py             # update_pnl_and_stats()
      exporters.py           # export_metrics() в CSV/Parquet (BQ/Grafana позже)
      alerts.py              # Telegram-алерты по DD/slippage/серии SL

    pipelines/
      backtest_offline.py    # оффлайн-бэктест только по файлам
      paper_realtime.py      # real-time paper: Helius -> симуляция (без реальных ордеров)
      daily_report.py        # отчёт за день (GitHub Actions)

  notebooks/
    01_dune_exploration.ipynb
    02_feature_playground.ipynb
    03_model_training.ipynb

  scripts/
    run_backtest.sh
    run_realtime_paper.sh

  requirements.txt
  README.md
  LICENSE
```

---

## 2) Контракты данных и типов (ядро всего)

Критично, чтобы все модули говорили на одном языке. Ниже — канонический набор (поля можно расширять, но **не ломать**).

### 2.1 `Trade` — нормализованное событие on‑chain

- минимальный набор: `ts, wallet, token_mint, side, size_usd`
- расширения: `size_token`, `platform`, `tx_hash`, `pool_address`

### 2.2 `WalletProfile` — профиль “лидера”

- ROI на окнах, винрейт, частота, средний размер, предпочтения DEX, роль (sniper/deployer/follower)

### 2.3 `TokenState` — снапшот состояния токена/пула

- цена, ликвидность, объёмы, depth на 1%/5%, honeypot flag

### 2.4 `Signal` — решение стратегии (после gates)

- включает выход модели: `p_model`, `edge` и выбранный режим/TTL/размер

### 2.5 `Position` — позиция для симуляции/учёта

- поддерживает partial exits (remaining_size), peak_price, причины выхода

> Примечание: в `Strategy Pack` runnable‑MVP хранит урезанную версию типов, но **совместимую** (см. `MVP_OFFLINE/src/core/types.py`).

---

## 3) “Мэппинг функций по файлам” (чтобы можно было начинать пилить)

### 3.1 Ingestion

`src/ingestion/dune_fetch.py`
- `fetch_top_wallets()` — Dune SQL → CSV/DF → фильтры Tier (например `ROI_30d > 0.2`, `trades_30d >= 50`)

`src/ingestion/helius_listener.py`
- `monitor_wallets_realtime(wallets: list[str]) -> iterator[Trade]`
- Helius webhook/gRPC → нормализация в `Trade`
- (опционально) failover на Alchemy/другого провайдера

`src/ingestion/dex_price_feeds.py`
- `fetch_token_state(token_mint: str) -> TokenState`
- Jupiter quote + Raydium пул + Birdeye/Dexscreener
- кэш 5–15 секунд

### 3.2 Features + ML

`src/features/wallet_profile.py`
- `build_wallet_profiles(trades_df) -> dict[str, WalletProfile]`
- `update_wallet_profile(existing_profile, new_trades)`

`src/features/token_features.py`
- `update_token_state_from_trade(trade: Trade) -> TokenState`

`src/features/trade_features.py`
- `build_features(trade: Trade, wp: WalletProfile, ts: TokenState) -> dict`

`src/models/train_xgboost.py`
- обучение XGBoost, сохранение в `models/artifacts/`

`src/models/predict.py`
- `predict_success(features: dict) -> tuple[p_model, edge]`

`src/models/survival.py` (опционально)
- `predict_exit_hazard(...) -> float`

### 3.3 Strategy

`src/strategy/mode_selector.py`
- `choose_scalp_mode(wallet_profile, current_price_change, time_from_entry_sec) -> str`
- конфиги U/S/M/L (+ агрессия) живут в `config/modes.yaml`

`src/strategy/risk_engine.py`
- `compute_position_size(bankroll_usd, edge, kelly_fraction=0.25) -> float`
- `apply_risk_limits(signal, portfolio_state) -> Optional[Signal]`

`src/strategy/honeypot_filter.py`
- `is_honeypot_safe(token_mint: str) -> bool` (GMGN + on-chain: freeze/taxes/…)

`src/strategy/exits.py`
- `apply_partial_take_profit(position, current_price)`
- `trailing_stop_check(position, current_price)`
- `should_close_full(position, current_price, now_ts) -> (bool, reason)`

### 3.4 Execution / Simulation

`src/execution/simulator.py`
- `simulate_fill_limit_ttl(signal, trades_stream, pool_state) -> fill_result`
- `simulate_exit(position, price_path, wallet_exits) -> Position`

`src/execution/queues.py`
- `queue_parallel_trades(signals)`
- `take_next_order_for_dex(dex_name) -> Signal|None`
- сначала можно in‑memory, потом Redis/Upstash free

`src/execution/live_executor_stub.py`
- заглушка “что бы отправили”, но фактически прокидываем в `simulator`

### 3.5 Monitoring / Pipelines

`src/monitoring/metrics.py`
- `update_pnl_and_stats(positions) -> dict` (PnL/ROI/DD/winrate по режимам/DEX/кошелькам)

`src/monitoring/exporters.py`
- экспорт в CSV/Parquet

`src/monitoring/alerts.py`
- Telegram: drawdown / серия SL / аномальный slippage

`src/pipelines/backtest_offline.py`
- история → Trade stream → Signal → fill/exit sim → метрики/экспорт

`src/pipelines/paper_realtime.py`
- live events → тот же пайп → **симуляция** (без реальных ордеров)

---

## 4) Сквозной runtime‑конвейер (явно)

**Listener → Normalizer(Trade) → Enrichment(WalletProfile + TokenState) → Features → Predict(p_model, edge) → Gates(honeypot/liquidity/slippage) → Mode + Risk → ExecutionSim(fill + exit) → Metrics + Export + Alerts**

---

## 5) Недельный план “MVP v0 на 0$” (реальный старт)

Цель: через ~7 дней иметь runnable `backtest_offline.py`, который гоняет **≥10k** событий и выдаёт PnL/ROI/DD/fill‑rate.

- **Д1–Д2:** каркас репо + types + Dune CSV reader + сбор Tier‑1 (200–300 кошельков)
- **Д3:** простой mode_selector + exits + грубый fill (константный slippage) + backtest “кривая equity”
- **Д4:** honeypot filter (минимум) + slippage через AMM + TTL режимов + гейт ликвидности
- **Д5:** фичи + XGBoost (минимально) + +EV правило `p_model/edge`
- **Д6:** риск (fractional Kelly/лимиты/kill‑switch) + лимит параллельных позиций + очередь
- **Д7:** метрики+экспорт + paper_realtime (Helius слушаем, но торгуем только в симе) + daily report

---

## 6) Критерии “готовой боевой v0” (Definition of Done)

1) `backtest_offline.py`:
- прогоняет **≥10k** событий
- считает **PnL / ROI / max drawdown / fill‑rate**
- сохраняет отчёт (CSV/Parquet)

2) `paper_realtime.py`:
- слушает **20–50** Tier‑1 кошельков (Helius)
- за сутки делает **≥100** симулированных входов/выходов
- пишет результаты (CSV/Parquet) + базовый daily report

---

## 7) (Опционально) “доноры/референсы” кода

Идея: внешние репозитории использовать как **доноров/референсы**, раскладывая по слоям:

- listener/ingestion → `src/ingestion/`
- Jupiter/Raydium routing → `dex_price_feeds.py` / `execution/`
- ML/фичи → `features/` + `models/`
- режимы/выходы/риск → `strategy/`
- метрики/отчёты → `monitoring/` + `pipelines/`

Документирует “куда что тащить”, но не фиксирует конкретные ссылки как обязательные зависимости.