# RESOURCES_AND_APPS (Free‑First Registry)

Канонический (машиночитаемый) реестр: `RESOURCES_AND_APPS.yaml`.

**Free‑first правило:** ядро должно работать на бесплатных ресурсах / free tier / trial ≥ 7 дней.

**Research-only:** UI‑терминалы (BullX/GMGN/Axiom) не используются для исполнения.

## Core resources

- **Helius** — rpc/webhooks — free_first: `YES`
  - https://www.helius.dev/
  - Realtime wallet monitoring + decoded transactions (webhooks). Use rate limiting + caching.
- **Alchemy (Solana)** — rpc — free_first: `YES`
  - https://www.alchemy.com/solana
  - Secondary/failover RPC provider; keep a fallback to avoid SPOF.
- **Public Solana RPC** — rpc — free_first: `YES`
  - https://docs.solana.com/api/http
  - Last-resort fallback (limited, less reliable).
- **Solana Explorer** — explorer — free_first: `YES`
  - https://explorer.solana.com/
  - Official explorer for debugging tx/slots.
- **Solscan** — explorer — free_first: `YES`
  - https://solscan.io/
  - Explorer + some APIs (rate-limited). Good for manual research.
- **SolanaFM** — explorer — free_first: `YES`
  - https://solana.fm/
  - Explorer with decoding/UX; useful for manual debugging.
- **Kolscan** — wallet tracker/leaderboards — free_first: `YES`
  - https://kolscan.io/
  - Seed lists of “smart wallets” + basic PnL/leaderboards (use as discovery only; always verify on-chain).

- **Covalent** — web3 API/indexer — free_first: `YES`
  - https://www.covalenthq.com/
  - Convenience endpoints “wallet → tx/swaps”. Treat as replaceable; never a SPOF.

- **Moralis** — web3 API/indexer — free_first: `YES`
  - https://moralis.io/
  - Another replaceable indexer for history/enrichment. Use strict caching/limits.

- **DuckDB + Parquet** — storage — free_first: `YES`
  - https://duckdb.org/
  - Local analytics store for MVP/backtests; fast + portable.
- **Google Colab** — compute — free_first: `YES`
  - https://colab.research.google.com/
  - Week-1 default environment for notebook R&D and backtests.
- **Solana Beach** — explorer — free_first: `YES`
  - https://solanabeach.io/
  - Alternate explorer/metrics; useful for network health debugging.

## Data sources

- **Dune + Spellbook** — analytics — free_first: `YES`
  - https://dune.com/
  - Wallet discovery + SQL; export to CSV/Parquet for local processing.
- **Jupiter Quote API** — dex_aggregator — free_first: `YES`
  - https://dev.jup.ag/
  - Canonical slippage_est(size) + routing; use caching and respect limits.
- **Raydium docs/SDK** — dex — free_first: `YES`
  - https://docs.raydium.io/
  - AMM pool state + impact model for Raydium coverage.
- **Orca Whirlpools docs/SDK** — dex — free_first: `YES`
  - https://dev.orca.so/
  - Optional DEX coverage (concentrated liquidity).
- **Meteora docs (DLMM)** — dex — free_first: `YES`
  - https://docs.meteora.ag/
  - Optional DEX coverage (DLMM).
- **Birdeye (public API)** — market_data — free_first: `YES`
  - https://birdeye.so/
  - Prices/liquidity snapshots with rate limits; keep fallback sources.
- **Pyth Network price feeds (Solana)** — oracle — free_first: `YES`
  - https://docs.pyth.network/
  - SOL/USD and other feeds for qty_usd normalization + PnL reference.
- **Helius DAS (Digital Asset Standard)** — asset_metadata — free_first: `YES`
  - https://www.helius.dev/docs/api-reference/das/getassetsbyowner
  - Owner->assets, token metadata flags; useful for wallet context and token metadata.
- **Metaplex DAS (spec/SDK)** — spec/sdk — free_first: `YES`
  - https://docs.metaplex.com/
  - Portable DAS layer to avoid vendor lock-in.
- **Flipside (decoded Solana data)** — analytics — free_first: `YES`
  - https://flipsidecrypto.xyz/
  - Alternative decoded history; optional backfill channel.
- **Bitquery (Solana GraphQL)** — analytics — free_first: `MAYBE`
  - https://bitquery.io/
  - Optional accelerator for complex backfills (pricing may change). Never SPOF.
- **Polymarket (CLOB, read-only)** — macro_overlay — free_first: `YES`
  - https://docs.polymarket.com/
  - Risk regime overlay: pm_bullish_score + pm_event_risk. Poll slowly + cache.
- **Dexscreener** — market_data — free_first: `YES`
  - https://dexscreener.com/
  - Quick price/liquidity/volume snapshots. Treat as optional (rate limits/terms).
- **GeckoTerminal** — market_data — free_first: `YES`
  - https://www.geckoterminal.com/
  - Price/liquidity snapshots across DEXes. Optional fallback for token_snapshot.
- **Shyft (Solana APIs)** — api — free_first: `MAYBE`
  - https://shyft.to/
  - Optional decoded tx / indexing provider; pricing can change. Do not depend on it.

## Infra & storage

- **Upstash Redis** — cache/queue — free_first: `YES`
  - https://upstash.com/
  - Free tier for caching/streams; optional in week-1 (local Redis ok).
- **Redis (local / docker)** — cache/queue — free_first: `YES`
  - https://redis.io/
  - Local queues + caching; simplest infra.
- **BigQuery sandbox** — warehouse — free_first: `YES`
  - https://cloud.google.com/bigquery
  - Optional analytics store; good for dashboards/SQL. Avoid overkill week-1.
- **GitHub Actions** — automation — free_first: `YES`
  - https://github.com/features/actions
  - Cron-like jobs for ingestion/backtests on free tier for small runs.

## Dashboards & alerts

- **Grafana OSS (local)** — dashboard — free_first: `YES`
  - https://grafana.com/oss/grafana/
  - Local dashboards; can read from CSV/Parquet/Prometheus.
- **Grafana Cloud (free tier)** — dashboard — free_first: `YES`
  - https://grafana.com/products/cloud/
  - Optional hosted dashboards with free tier.
- **Telegram Bot API** — alerts — free_first: `YES`
  - https://core.telegram.org/bots/api
  - Daily report + alerts; simplest notification channel.

## Learning & reference

- **Solana JSON-RPC docs** — docs — free_first: `YES`
  - https://solana.com/docs/rpc
  - RPC methods/limits; understand commitment/finality.
- **Solana Cookbook** — docs — free_first: `YES`
  - https://solanacookbook.com/
  - Practical snippets for programs/clients.
- **SPL Token docs** — docs — free_first: `YES`
  - https://spl.solana.com/token
  - Authorities, freeze/mint, transfer rules; core for honeypot checks.
- **Token-2022 docs (extensions)** — docs — free_first: `YES`
  - https://spl.solana.com/token-2022
  - TransferHook / extensions useful for risk checks.
- **Jito docs (reference)** — docs/mev — free_first: `YES`
  - https://docs.jito.wtf/
  - Week-1: reference only; later for priority/bundles modeling/upgrades.

## Optional upgrades

- **Private/paid RPC** — rpc — free_first: `NO`
  - Only after proven edge; improves reliability + latency.
- **Jito bundles / tips** — mev — free_first: `NO`
  - Optional execution accelerator; not needed for week-1 MVP.
- **Paid terminals (BullX/GMGN/Axiom)** — ui — free_first: `NO`
  - Research-only; never core execution path.

## Notes

- В ядре стратегии любые внешние источники подключаются через адаптеры и легко заменяются.
- Сервисы с лимитами: всегда используем кэш + rate limiting + retries/backoff.
- Источники с free_first=MAYBE не должны становиться SPOF: используем только как ускорители/бекфиллы.
