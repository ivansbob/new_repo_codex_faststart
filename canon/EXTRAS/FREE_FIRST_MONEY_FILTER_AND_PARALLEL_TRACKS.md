# Free‑First Money Filter + Parallel Tracks (Data‑track vs Bot‑track)

Этот документ фиксирует два важных дополнения к стратегии:

1) **Money‑Filter**: что можно положить в “ядро” прямо сейчас при ограничении *free ≥ 7 дней*  
2) **Боевая схема параллельной сборки**: как одновременно строить **датапайплайн** и **paper‑бота**, не мешая одно другому.

> Контекст: Golden Mean Exit Engine (GMEE) — “золотой движок” эволюции стратегии.  
> Strategy Pack хранит спецификацию, контракты и артефакты, чтобы Codex мог превращать их в код.

---

## 1) Money‑Filter (free ≥ 7 дней)

### Green (в ядро без оговорок)
- **DuckDB + Parquet** (локальная DWH/аналитика, бэктесты)
- **Python OSS**: pandas/polars, numpy, scikit‑learn, xgboost/lightgbm, lifelines, networkx
- **Telegram Bot API** (алерты/репорты)
- **Colab / Kaggle** (тренировки/симуляции; квоты — ок для MVP)

- **Kolscan** (free‑first): seed‑кошельки/лидерборды
- **Polymarket (Gamma/CLOB, read‑only)**: внешний режим рынка (risk_regime)

### Amber (в ядро можно, но строго с кэшем/лимитами/фейловером)
- **Helius** (free tier): realtime‑стрим по Tier‑1 + батчи по остальным
- **Alchemy** (free tier): fallback RPC, защита от 429 / деградаций
- **BigQuery Sandbox**: бесплатно, но ограничено (например, без streaming insert)
- **Upstash Redis (free)**: очереди/кэш на старте; затем можно заменить локальным Redis
- **Grafana Cloud (free)** или **Grafana OSS локально**
- **Jupiter APIs**: quote/route для оценки цены/слиппеджа (только через кэш)
- **DEXScreener / Birdeye**: как *sanity‑check* (не делаем их SPOF)


- **Dune / Flipside**: SQL‑лидерборды (выгрузки/квоты зависят от плана)
- **SolanaFM API**: удобное декодирование/выборки (rate‑limited)
- **Covalent / Moralis**: готовые endpoints “wallet → tx/swaps” (free tiers)

### Красная зона (в неделю 1 не делаем ядром)
- **UI‑терминалы (BullX/GMGN/Axiom)**: только research, не ядро (fee/комиссии и lock‑in)
- **Live‑исполнение с “fee warfare”** (priority fees / Jito bundles) — в неделю 1 **OFF**.  
  Вместо этого: моделируем latency/MEV в симуляции и обкатываем risk‑ограничители.

---

## 2) Поправка про Dune (важно для free‑first)
Dune удобно для **discovery и SQL**, но **CSV‑экспорт может быть ограничен планом**.
Практика для free‑first:
- Dune = discovery/валидатор гипотез
- Выгрузки = через API export (если доступно) / альтернативы (Flipside/BigQuery) / ручные лимитированные экспорты

---

## 3) Карта данных: что нужно и откуда брать

### 3.1 История кошельков (profiling)
Нужно: ROI_7/30/90, winrate, trades_count, median_hold_sec, avg_size_usd, preferred_dex, роль (sniper/deployer/follower), граф follower→leader.

Источники (free‑first):
- Dune / Flipside / BigQuery public datasets
- локально: DuckDB+Parquet (канонический storage)

Артефакты:
- `data/processed/wallet_profile.parquet`
- `data/processed/wallet_tiers.json`
- `data/processed/wallet_graph.parquet|json`

### 3.2 Realtime сделки Tier‑1
Нужно: нормализованный `Trade`:
`ts, wallet, token_mint, side, size_token, size_usd, platform, tx_hash, pool_address`.

Источники:
- Helius (primary)
- Alchemy (fallback)

Артефакты:
- очередь `trade_events`
- `data/raw/trade_events_*.parquet`

### 3.3 Token/Pool snapshots (цена/ликвидность/глубина)
Нужно: price, liquidity_usd, volume_5m/30m/24h, depth_1pct/5pct, spread_bps, holders концентрации, honeypot flags.

Источники:
- Jupiter quote/route
- Raydium/Orca/Meteora SDK
- Dexscreener/Birdeye как sanity

Артефакты:
- `data/processed/token_snapshot.parquet`

### 3.4 Honeypot / Rug gates
Нужно: freezeAuthority, blacklist признаки, taxes, sellability.

Источники:
- on‑chain проверки через RPC
- (опционально) внешние flags (GMGN и т.п.) как “доп‑сигнал”, но не SPOF

Артефакты:
- `data/processed/token_risk_flags.parquet`

---

## 4) Боевая схема: два трека параллельно

### Track A — Data‑track (производит “топливо”)
A1. **Wallet profiler (daily/nightly):** история → wallet_profile + tiers + graph  
A2. **History builder (batch):** сделки Tier‑universe → trades_norm.parquet  
A3. **Token snapshot cache:** периодические snapshots → token_snapshot.parquet

### Track B — Bot‑track (производит PnL/метрики)
B1. **Realtime listener:** Helius → очередь `trade_events`  
B2. **Scorer+Simulator workers (N воркеров):**
`trade_event → enrich/cache → features → (model) → signal → sim fill/exit → positions/pnl`  
B3. **Metrics+Reports:** DuckDB views → Grafana + Telegram

Ключевой принцип:
- Data‑track может лагать/падать, а Bot‑track не должен “умирать”.
- При деградации: меньше фич/реже snapshots, но **пайплайн продолжает работать**.

---

## 5) Free‑cap правила (чтобы не упереться в лимиты)
- Realtime слушаем только **Tier‑1 (старт 200–300)**; остальных — батчами.
- Все внешние API — **кэш 5–15s + rate limiting + retry/backoff**.
- Нет SPOF: Helius primary, второй RPC fallback; snapshots: Jupiter + DEX SDK; sanity: Dexscreener/Birdeye.
- Неделя 1: **Jito = OFF**, priority fees = 0 (или минимально). Только симуляция latency/MEV.

---

## 6) Каноническая конфигурация
- `config/params_base.yaml` — единый источник правды (v3.0)
- `config/modes.yaml` — вынесенная часть про U/S/M/L + aggressive (для удобства)

MVP_OFFLINE умеет читать `params_base.yaml` и **нормализовать** его в компактный вид для текущего сим‑пайплайна.

---

## Canonical configuration
- Canonical GMEE/Codex config: `config/params_base.yaml` (v3.0)
- Convenience extraction: `config/modes.yaml`

## Dune nuance (free-first)
Dune удобен для discovery/SQL, но **экспорт данных зависит от плана** (например, CSV export может быть платным).
Поэтому не делаем Dune единственной “CSV-трубой”: ingestion должен уметь жить через API exports / альтернативные источники / ограниченный ручной экспорт.


---

## Reference links
- Telegram Bot API / Platform docs: https://core.telegram.org
- Google Colab FAQ: https://research.google.com/colaboratory/faq.html
- Helius plans/pricing: https://www.helius.dev/docs/billing/plans
- Alchemy pricing: https://www.alchemy.com/pricing
- BigQuery Sandbox: https://cloud.google.com/bigquery/docs/sandbox
- Upstash Redis pricing/limits: https://upstash.com/docs/redis/overall/pricing
- Grafana Cloud usage limits: https://grafana.com/docs/grafana-cloud/cost-management-and-billing/manage-invoices/understand-your-invoice/usage-limits/
- Jupiter developer portal (rate limits): https://dev.jup.ag/portal/rate-limit
- DEX Screener API reference: https://docs.dexscreener.com/api/reference
- Birdeye API rate limiting: https://docs.birdeye.so/docs/rate-limiting
- Dune export data out: https://docs.dune.com/learning/how-tos/export-data-out
