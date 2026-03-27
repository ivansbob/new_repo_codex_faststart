# Solana Copy‑Scalping (Free‑First) — Strategy Kernel v1

## 0) Скоуп
**Что строим:** автоматический copy‑scalping мемкоинов в Solana:
*watch wallets → normalize events → features/ML → +EV signals → simulate/execute → risk → metrics/dashboard*.

**Free‑first правило:** всё ядро запускается на бесплатных ресурсах (или free trial/credits ≥ 7 дней).
Платные ускорители (private RPC, Jito tips, платные терминалы) — только как опциональные апгрейды после доказанного edge.

**Не делаем в ядре:** торговлю через платные телеграм‑терминалы (GMGN/BullX/Axiom и т.п.) — используем их максимум как «визуальный ресёрч», но исполнение — напрямую через DEX/агрегатор.

---

## 1) Две параллельные дорожки

### 1.1 Data‑track (история + поток)
**Цель:** быстро получить *wallet_metrics* + *trades* в одном формате.

* История: выгрузки из аналитики/SQL → DuckDB/Parquet.
* Поток: realtime events по Tier‑1 кошелькам → тот же формат → DuckDB/Parquet.

### 1.2 Bot‑track (каркас)
**Цель:** сервисный пайплайн без реальных ордеров на первом этапе.

* Listener → Normalizer → FeatureBuilder → SignalEngine → Simulator → Metrics.
* Включаем paper‑trading, потом микросуммы.

---

## 2) Единый формат событий (data contract)

### 2.1 trade_event (нормализованный)
* `ts_block` (UTC)
* `wallet`
* `mint`
* `side` (BUY/SELL)
* `qty_token`
* `qty_usd` (если нет — пересчёт через price snapshot)
* `price` (mid/quote)
* `platform` (raydium/jupiter/pumpfun/…)
* `tx_hash`
* `slot`

### 2.2 token_snapshot
* `ts`
* `mint`
* `price`
* `liquidity_usd`
* `volume_5m`, `volume_1h`, `volume_24h`
* `depth_bps_100`, `depth_bps_300` (опционально)
* `spread_bps` (если есть)

### 2.3 wallet_profile
* `wallet`
* `roi_7d`, `roi_30d`, `roi_90d`
* `winrate_30d`
* `trades_30d`
* `median_hold_sec`
* `avg_size_usd`
* `preferred_dex`
* `cluster_label` (sniper/deployer/follower/…)

### 2.4 signal
* `signal_id`
* `ts`
* `wallet`
* `mint`
* `mode` (U/S/M/L)
* `entry_price`, `limit_price`, `ttl_sec`, `max_slippage_bps`
* `p_model`, `edge_raw`, `edge_final`
* `risk_regime` (overlay)
* `decision` (ENTER/SKIP)

---

## 3) Реестр параметров (defaults, которые не теряем)

### 3.1 Universe & фильтры
* `min_liquidity_discovery_usd = 2_000–5_000`
* `min_liquidity_trade_usd = 15_000–50_000` (строже для реальных входов)
* `max_spread_bps = 80–150`

### 3.2 +EV
* `edge_threshold_base = 0.05` (рабочий дефолт)
* `edge_threshold_riskon = 0.03` (если overlay bullish)
* `edge_threshold_riskoff = 0.07` (если overlay bearish)

### 3.3 Режимы скальпа
* **U:** hold 15–30s, TP +2.5%, SL −2.5%
* **S:** hold 60–90s, TP +5%, SL −4.5%
* **M:** hold 120–180s, TP +9%, SL −7%
* **L:** hold 240–300s, TP +14%, SL −10%

### 3.4 TTL / исполнение
* `ttl_sec_by_mode = {U: 15–30, S: 60–120, M: 120–180, L: 180–300}`
* `max_slippage_bps = 50–200` (симуляция) / `10–50` (консервативный live)
* Цель по симуляции: `fill_rate_target = 0.70–0.85`

### 3.5 Риск‑менеджмент
* `position_pct = 0.5–2%` банка (по умолчанию)
* `kelly_fraction = 0.25`
* `max_open_positions = 10–30`
* `max_token_exposure = 20–30%`
* `max_daily_loss = 10–20%`
* `max_drawdown = 25%` → kill‑switch
* `cooldown_after_losses` (например, 15–60 мин)

---

## 4) Алгоритмы (каноническое описание)

### 4.1 Signal score
1. Hard gates: liquidity, spread, honeypot_safe.
2. `p_model = model(features)` + калибровка.
3. `edge_raw = expected_value(p_model, payoff_model)`.
4. `risk_regime ∈ [-1; +1]` (overlay).
5. `edge_final = edge_raw * (1 + alpha * risk_regime)`.
6. ENTER если `edge_final > edge_threshold(regime)`.

### 4.2 Execution simulator (limit+TTL)
* Берём поток трейдов/квот в окне TTL.
* Исполняем частями по доступной ликвидности.
* Учитываем AMM impact и маршрут агрегатора.
* Выход: TP/SL/time‑cap/reverse.

### 4.3 Aggressive trigger + partial
* Если быстрый импульс (например, +3% за 12с в U), то:
  * фиксируем 30–50% позиции,
  * остаток переводим в trailing (10–15% от пика),
  * TTL/SL делаем агрессивнее.

### 4.4 Wallet graph / chain reaction (опционально)
* Строим граф «кто за кем ходит».
* Если лидер (in‑degree>3) выходит, повышаем hazard выхода для фолловеров.

---

## 5) Polymarket overlay (внешний мозг‑сентимент)

**Роль:** Polymarket **не генерирует сделки** и не “предсказывает мемкоины”. Он играет роль **внешнего оракула настроения/сценариев**, который отвечает на вопрос:

> *“Сейчас вообще стоит агрессивно копировать Solana‑мемкоины или лучше притормозить?”*

### 5.1 Что берём (только free, read‑only)
Используем только публичные read‑only API Polymarket:
- **Gamma (Markets API)**: discovery рынков/ивентов, текущие цены, объёмы.
- **CLOB snapshot** (если нужно): bid/ask/spread для корректировки на микроструктуру.

**Ключ:** мы **не торгуем** на Polymarket; берём только данные для оверлея.

### 5.2 Как считаем вероятности (implied probability)
Для выбранных рынков берём цены YES/NO и считаем implied‑вероятность:
- `p_yes = price_yes / (price_yes + price_no)`  
- при наличии bid/ask: считаем `p_mid` по mid‑ценам и логируем `spread` как “сигнал качества”.

### 5.3 Какие рынки используем (минимальный “макро‑набор”)
**Regime‑filter рынки** (примерные категории):
- “BTC/ETH выше/ниже уровня к дате”
- “Crypto market cap up/down”
- крупные политико‑регуляторные события, которые часто двигают риск‑аппетит

Важно: список рынков — **конфиг**, а не код (легко заменять, не делая Polymarket SPOF).

### 5.4 Risk regime scalar `risk_regime ∈ [-1; +1]`
Переходим от набора вероятностей к одному скаляру режима:
- собираем фичи `z`: `Δp_1h`, `Δp_24h`, `volume_z`, (опц.) “event_risk”
- агрегируем: `risk_regime = clip(tanh(w·z), -1, +1)`

Интуиция:
- `risk_regime > 0` → **risk‑on** (можно мягче пороги/больше size)
- `risk_regime < 0` → **risk‑off** (жестче фильтры/меньше size/выключаем агрессию)

### 5.5 Как это влияет на Solana copy‑scalping (строго канон)
1) **Порог входа**:
- `edge_threshold = δ_base + k_δ * (-risk_regime)`  
  (risk‑off → δ выше; risk‑on → δ ниже)

2) **Размер позиции**:
- `pos_pct = clamp(pos_base * (1 + k_size * risk_regime), pos_min, pos_max)`

3) **Режимы U/S/M/L**:
- risk‑on: допускаем больше U/S, TTL чуть шире (если ликвидность позволяет)
- risk‑off: смещаемся в S/M (или вообще SKIP), TTL короче, требования к ликвидности/спреду строже

4) **Aggressive Layer (“rocket mode”)**:
- `risk_regime < r_off` → агрессивный слой **запрещён**
- `risk_regime > r_on` → агрессивный слой **разрешён**, но только после safety‑гейтов

### 5.6 Narrative overlay (ивенты → нарративы → мемкоины)
Если вероятность события на Polymarket **резко растёт**, это может усиливать вес связанных нарративов:
- `event → narrative_tag → token_tag`
- эффект только как **мультипликатор веса** (например, +10–30% к score), но не как самостоятельный сигнал.

### 5.7 Sanity check (диагностика модели)
Polymarket даёт независимый взгляд:
- если модель/кошельки “ломятся в лонг”, а `risk_regime` устойчиво отрицательный → это красный флаг  
  (жёстче пороги, уменьшаем size, включаем cooldown).

### 5.8 Логирование (обязательно)
Пишем витрину влияния оверлея:
- `pmkt_snapshot_id`, `risk_regime`, `edge_raw`, `edge_final`, `delta_used`, `pos_pct_used`, `decision`.

Это даёт объяснимость: **как именно Polymarket изменил решение**.

---

## 6) План исполнения (батчами по 10 пунктов)

### 0–10: уже зафиксированное ядро
0. Repo‑вендоринг + структура проекта.
1. Таблицы DuckDB/Parquet.
2. Dune/Kolscan экспорт Tier‑list.
3. Нормализатор trade_event.
4. Token snapshots.
5. Первичный симулятор fill+TTL.
6. Метрики ROI/fill_rate/drawdown.
7. Дашборд (минимальный).
8. Honeypot gates (первичные).
9. Baseline rules (без ML).
10. Walk‑forward backtest каркас.

### 11–20: усиление (overlay+ML)
11. Polymarket snapshot collector → pmkt_snapshots.
12. Risk_regime вычисление + логирование.
13. Интеграция regime в signal engine (threshold/size).
14. FeatureBuilder v1 (vol/impulse/liquidity/wallet ctx).
15. Model training (TimeSeriesSplit + calibration).
16. Survival exits (hazard P(exit≤30–60s)).
17. Partial TP + trailing.
18. Wallet clustering v1 (rule‑based → потом ML).
19. Strategy leaderboard (параметры → метрики).
20. Paper‑trading loop (без отправки tx).

### 21–30: боевой каркас
21. Очереди/идемпотентность ордеров.
22. RPC batching + кэш.
23. Failover RPC.
24. Расширение DEX coverage.
25. Строгие honeypot checks (simulate buy/sell).
26. Anti‑MEV (защитные настройки; без атакующих стратегий).
27. Micro‑live (малые суммы, мало кошельков).
28. Авто‑ретрейн / дрейф.
29. Kill‑switch/операторская консоль.
30. Масштабирование Tier‑list.

---

## 7) Как мы дальше «склеиваем» чат
Чтобы не потерять смысл при больших кусках текста:
1. Ты кидаешь следующий фрагмент.
2. Я добавляю только **новые** параметры/функции в этот документ (как patch‑notes).
3. Если что‑то конфликтует — фиксируем в «реестре параметров» (одна правда).

---

## 8) Дополнительные ресурсы (Free‑First), которые стоит учитывать в реализации

Это **не обязательные зависимости**, а “ускорители”, которые можно подключать как адаптеры/провайдеры, чтобы не душить RPC и быстрее строить snapshots/проверки.

### 8.1 Ончейн‑эксплореры (дебаг/ресёрч)
* Solana Explorer (официальный)
* Solscan
* SolanaFM

### 8.2 Декод транзакций и метаданные ассетов
* Helius Transactions API / Webhooks (удобный декод)
* Helius DAS / Digital Asset Standard (assets/metadata/owner->assets)
* Metaplex DAS (спека/SDK) — как переносимый слой “asset provider”

### 8.3 Маркет‑данные и котировки
* Dexscreener / GeckoTerminal — быстрые снапшоты (как optional fallback, не SPOF)

* Jupiter Quote API (slippage_est, routes)
* Raydium API/SDK (AMM pools)
* Orca Whirlpools (если покрываете Orca)
* Meteora (DLMM) (если покрываете Meteora)

### 8.4 USD‑прайсинг и эталонные фиды
* Pyth Network (SOL/USD и др.) — для нормализации qty_usd и PnL

### 8.5 Исторические источники/бекфиллы (чтобы меньше упираться в RPC)
* Dune / Spellbook
* Flipside (decoded Solana data)
* Bitquery (GraphQL) — optional, как ускоритель сложных выборок

### 8.6 Safety / rug‑скрининг (как внешние “подсказки”)
* RugCheck (sanity‑check токена) — только как hint, не как SPOF
* SPL Token / Token‑2022 extensions (freeze authority, transfer hooks) — on‑chain hard-gates

### 8.7 Документация разработчика
* Solana docs / JSON‑RPC spec
* SPL Token docs
* Token‑2022 docs (extensions)

### 8.8 MEV/Jito (позже)
* Jito Block Engine docs — полезно понимать latency/priority, но в week‑1 ядро не тащим.

Смотри также: **RESOURCES_AND_APPS.md / RESOURCES_AND_APPS.yaml** — это реестр “что разрешено в ядре” vs “что опционально”.