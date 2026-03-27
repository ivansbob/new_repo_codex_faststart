-- schemas/postgres.sql
-- GMEE P0 reproducibility & governance schema (v0.4)

-- config_store: canonical storage of normalized config YAML by hash
CREATE TABLE IF NOT EXISTS config_store (
  config_hash   CHAR(64) PRIMARY KEY,
  config_yaml   TEXT NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  created_by    TEXT,
  notes         TEXT
);
CREATE INDEX IF NOT EXISTS idx_config_store_created_at ON config_store (created_at DESC);

-- experiment_registry: reproducible runs (sim/paper/canary)
CREATE TABLE IF NOT EXISTS experiment_registry (
  experiment_id     UUID PRIMARY KEY,
  config_hash       CHAR(64) NOT NULL REFERENCES config_store(config_hash),
  chain             TEXT NOT NULL,
  env               TEXT NOT NULL, -- sim|paper|live|canary|testnet
  seed              BIGINT NOT NULL,
  started_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  ended_at          TIMESTAMPTZ,
  dataset_snapshot  TEXT,          -- CH snapshot / time window / query hash
  artifact_uri      TEXT,          -- s3://... or file://...
  metrics_json      JSONB NOT NULL DEFAULT '{}'::jsonb,
  bootstrap_lb      DOUBLE PRECISION,
  permutation_p     DOUBLE PRECISION,
  created_by        TEXT,
  notes             TEXT
);
CREATE INDEX IF NOT EXISTS idx_experiment_registry_chain_env_time ON experiment_registry (chain, env, started_at DESC);
CREATE INDEX IF NOT EXISTS idx_experiment_registry_config_hash ON experiment_registry (config_hash);

-- promotions_audit: signed audit trail of GO/NO-GO/rollback decisions
CREATE TABLE IF NOT EXISTS promotions_audit (
  promotion_id          BIGSERIAL PRIMARY KEY,
  ts                    TIMESTAMPTZ NOT NULL DEFAULT now(),
  chain                 TEXT NOT NULL,
  env                   TEXT NOT NULL, -- paper|live
  decision              TEXT NOT NULL, -- go|no_go|rollback
  promoted_config_hash  CHAR(64) NOT NULL REFERENCES config_store(config_hash),
  previous_config_hash  CHAR(64),
  approved_by           TEXT NOT NULL,
  ticket_ref            TEXT,
  reason                TEXT NOT NULL,
  artifact_uri          TEXT,
  details_json          JSONB NOT NULL DEFAULT '{}'::jsonb
);
CREATE INDEX IF NOT EXISTS idx_promotions_audit_chain_env_ts ON promotions_audit (chain, env, ts DESC);
CREATE INDEX IF NOT EXISTS idx_promotions_audit_promoted_hash ON promotions_audit (promoted_config_hash);
