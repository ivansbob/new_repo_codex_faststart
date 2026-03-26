# Master function inventory

## Intake
- load source data
- normalize trade rows
- validate against schema
- attach trace id
- parquet/jsonl/csv ingestion
- wallet seed import
- discovery ingest

## Pre-decision
- hard gates
- allowlist
- wallet tier
- mode resolution
- token snapshot lookup
- wallet profile lookup
- universal vars join
- calibrated model input build
- EV calculation
- Polymarket regime overlay

## Pre-execution
- sim preflight
- execution preflight
- route sanity
- slippage sanity
- latency sanity
- reject reason emission

## Decision/run
- signal engine
- paper pipeline
- position sizing
- bankroll caps
- kill switch
- exit plan parity
- order parameter formation

## Replay/calibration
- historical replay harness
- replay manifests
- replay reports
- chain backfill
- calibration grid
- leaderboard and recommender

## Execution/trading
- fill model
- friction model
- pnl engine
- position book
- position monitor
- trade logger

## Analytics/scoring
- unified score
- score router
- prescore
- smart wallet hits
- continuation enricher
- x validation score
- config suggestions
- analyzer metrics and reports

## Safety
- rug engine
- authority checks
- LP checks
- concentration checks
- dev risk checks
- evidence quality
- bundle evidence detection

## Wallet intelligence
- wallet graph builder
- wallet clustering
- wallet family metadata
- linkage scorer
- wallet registry score
- wallet replay validation

## Ops/reproducibility
- trade schemas
- signal schemas
- feature matrix schema
- bundle evidence schema
- smoke tests
- acceptance gates
- evidence bundle export
- trace investigation
- doctor command
- canary replay

## Sidecar control plane
- voice webhook
- ASR chunking
- transcript repair flow
- note distillation
- strict JSON next-pack
- model routing
- privacy ledger
- operator cockpit