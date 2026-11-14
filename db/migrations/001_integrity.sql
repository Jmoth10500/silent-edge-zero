-- Silent Edge Zero — data-integrity layer (migration 001, 2026-10-17)
--
-- STRICTLY ADDITIVE. Nothing here alters, drops or rewrites an existing
-- table, row, trigger or the frozen prediction/model_version DDL in
-- db/schema.sql (lines 207-269 are hash-frozen by scripts/check_model_freeze.py,
-- which is why this lives in its own file and not in schema.sql).
--
-- Layers (see docs/DATA_INTEGRITY.md):
--   1. RAW IMMUTABLE      race_feed_snapshot, market_price_snapshot, prediction_lock
--   2. VALIDATED/ELIGIBLE race_validation, race_integrity, canonical_race
--   3. DERIVED            bet_settlement, metric_snapshot
--   4. AUDIT              correction_ledger
-- Raw + audit tables are append-only: UPDATE/DELETE are rejected by trigger.
-- Safe to re-run (IF NOT EXISTS / CREATE OR REPLACE throughout).

CREATE OR REPLACE FUNCTION integrity_append_only() RETURNS trigger AS $$
BEGIN
    RAISE EXCEPTION '% on % is not allowed: table is append-only (insert a new row / ledger entry instead)',
        TG_OP, TG_TABLE_NAME;
END;
$$ LANGUAGE plpgsql;

-- ---------------------------------------------------------------- RAW --
-- Every racecard fetch, verbatim. Lets us replay "what did the provider say
-- at time T" and prove which snapshot a prediction was built from.
CREATE TABLE IF NOT EXISTS race_feed_snapshot (
    id              BIGSERIAL PRIMARY KEY,
    source          TEXT        NOT NULL,
    target_date     DATE        NOT NULL,
    fetched_at      TIMESTAMPTZ NOT NULL,
    payload         JSONB       NOT NULL,          -- normalised RaceCards as fetched
    payload_sha256  TEXT        NOT NULL,
    race_count      INT         NOT NULL,
    UNIQUE (source, target_date, fetched_at)
);
CREATE INDEX IF NOT EXISTS idx_feed_snapshot_date ON race_feed_snapshot(target_date, fetched_at);

-- Canonical, immutable race identity. canonical_race_id never changes;
-- scheduled_off_time is mutable metadata (reschedules UPDATE it, history is in
-- canonical_race_time_history).
CREATE TABLE IF NOT EXISTS canonical_race (
    canonical_race_id   TEXT PRIMARY KEY,           -- 'P:<provider race id>' or 'C:<date>|<course>|<sequence>'
    id_basis            TEXT NOT NULL CHECK (id_basis IN ('PROVIDER_ID', 'COMPOSITE')),
    meeting_id          TEXT NOT NULL,              -- '<date>|<normalised course>'
    provider_race_id    TEXT UNIQUE,                -- authoritative feed id (NULL only for COMPOSITE)
    race_date           DATE NOT NULL,
    course_id           INT  NOT NULL REFERENCES course(id),
    division            TEXT,                       -- 'I' / 'II' / NULL
    race_row_id         INT  REFERENCES race(id),   -- the legacy race row that represents it
    scheduled_off_time  TIME,                       -- CURRENT scheduled time (mutable)
    status              TEXT NOT NULL DEFAULT 'ACTIVE'
                        CHECK (status IN ('ACTIVE', 'RETIRED', 'QUARANTINED', 'ABANDONED')),
    first_seen_at       TIMESTAMPTZ NOT NULL,
    last_seen_at        TIMESTAMPTZ NOT NULL,
    last_snapshot_id    BIGINT REFERENCES race_feed_snapshot(id)
);
CREATE INDEX IF NOT EXISTS idx_canonical_race_date ON canonical_race(race_date, course_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_canonical_race_row ON canonical_race(race_row_id) WHERE race_row_id IS NOT NULL;

CREATE TABLE IF NOT EXISTS canonical_race_time_history (
    id                  BIGSERIAL PRIMARY KEY,
    canonical_race_id   TEXT NOT NULL REFERENCES canonical_race(canonical_race_id),
    scheduled_off_time  TIME NOT NULL,
    observed_at         TIMESTAMPTZ NOT NULL,
    snapshot_id         BIGINT REFERENCES race_feed_snapshot(id)
);

-- One row per (race, model) lock: the complete input snapshot a prediction
-- was made from, plus a hash proving it. Append-only.
CREATE TABLE IF NOT EXISTS prediction_lock (
    id                  BIGSERIAL PRIMARY KEY,
    race_id             INT  NOT NULL REFERENCES race(id),
    model_version_id    INT  NOT NULL REFERENCES model_version(id),
    canonical_race_id   TEXT,
    meeting_id          TEXT,
    source_race_id      TEXT,                       -- provider race id at lock
    feed_snapshot_id    BIGINT REFERENCES race_feed_snapshot(id),
    source_snapshot_at  TIMESTAMPTZ,
    scheduled_off_time  TIME NOT NULL,              -- as scheduled AT lock
    runner_ids          INT[]  NOT NULL,
    runner_names        TEXT[] NOT NULL,
    probabilities       JSONB  NOT NULL,            -- {horse_id: model_probability}
    locked_at           TIMESTAMPTZ NOT NULL,
    input_sha256        TEXT NOT NULL,
    provenance          TEXT NOT NULL CHECK (provenance IN ('LIVE_GATED', 'LEGACY_RECONSTRUCTED')),
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (race_id, model_version_id)
);

-- Immutable market price observations. Never overwritten; fallback and
-- primary rows are distinguished by source_type and is_fallback.
CREATE TABLE IF NOT EXISTS market_price_snapshot (
    id                  BIGSERIAL PRIMARY KEY,
    race_id             INT NOT NULL REFERENCES race(id),
    horse_id            INT NOT NULL REFERENCES horse(id),
    canonical_race_id   TEXT,
    source_name         TEXT NOT NULL,
    source_type         TEXT NOT NULL CHECK (source_type IN ('EXCHANGE', 'BOOKMAKER', 'WEB_FALLBACK')),
    is_fallback         BOOLEAN NOT NULL DEFAULT FALSE,
    back_price          NUMERIC,                    -- NULL means "no price", with null_reason
    lay_price           NUMERIC,
    available_volume    NUMERIC,
    captured_at         TIMESTAMPTZ NOT NULL,
    checkpoint          TEXT,                       -- LOCK / T-30 / T-15 / T-5 / T-1 / ADHOC
    secs_rel_lock       INT,
    secs_rel_off        INT,
    api_status          TEXT,
    null_reason         TEXT,
    fallback_reason     TEXT,
    job_id              TEXT,
    legacy_market_snapshot_id INT,                  -- set when mirrored from market_snapshot
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (back_price IS NOT NULL OR null_reason IS NOT NULL)
);
CREATE INDEX IF NOT EXISTS idx_mps_race ON market_price_snapshot(race_id, horse_id, captured_at);
CREATE UNIQUE INDEX IF NOT EXISTS uq_mps_legacy ON market_price_snapshot(legacy_market_snapshot_id)
    WHERE legacy_market_snapshot_id IS NOT NULL;

-- --------------------------------------------------- VALIDATED / ELIGIBLE --
-- Append-only validation verdicts. The latest row per race_id is current.
CREATE TABLE IF NOT EXISTS race_validation (
    id                  BIGSERIAL PRIMARY KEY,
    race_id             INT NOT NULL REFERENCES race(id),
    canonical_race_id   TEXT,
    validated_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
    status              TEXT NOT NULL CHECK (status IN ('VALID', 'QUARANTINED')),
    failed_rules        TEXT[] NOT NULL DEFAULT '{}',
    detail              JSONB,
    feed_snapshot_id    BIGINT REFERENCES race_feed_snapshot(id),
    raw_payload         JSONB                       -- raw source payload retained for debugging
);
CREATE INDEX IF NOT EXISTS idx_race_validation_race ON race_validation(race_id, validated_at);

-- Current integrity classification per historical/live race. Derived and
-- re-computable; every change is mirrored in correction_ledger.
CREATE TABLE IF NOT EXISTS race_integrity (
    race_id             INT PRIMARY KEY REFERENCES race(id),
    classification      TEXT NOT NULL CHECK (classification IN (
        'VALID', 'INVALID_DUPLICATE', 'INVALID_RACE_ID', 'MISSING_RESULT',
        'MISSING_MARKET', 'NON_RUNNER', 'OTHER')),
    include_in_metrics  BOOLEAN NOT NULL,
    has_result          BOOLEAN NOT NULL,
    has_lock_market     BOOLEAN NOT NULL,
    reason              TEXT NOT NULL,
    evidence            JSONB,
    run_id              TEXT NOT NULL,
    classified_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Convenience: races the metrics layer must never count.
CREATE OR REPLACE VIEW excluded_race AS
    SELECT race_id FROM race_integrity WHERE NOT include_in_metrics;

-- ------------------------------------------------------------- DERIVED --
CREATE TABLE IF NOT EXISTS bet_settlement (
    race_id                 INT NOT NULL REFERENCES race(id),
    model_version_id        INT NOT NULL REFERENCES model_version(id),
    horse_id                INT NOT NULL REFERENCES horse(id),
    settlement_price        NUMERIC,
    settlement_price_type   TEXT NOT NULL CHECK (settlement_price_type IN (
        'EXCHANGE_LOCK', 'EXCHANGE_OTHER', 'SP', 'NO_PRICE')),
    price_timestamp         TIMESTAMPTZ,
    price_source            TEXT,
    result_status           TEXT NOT NULL,
    stake                   NUMERIC NOT NULL,
    gross_return            NUMERIC,
    commission              NUMERIC NOT NULL DEFAULT 0,
    net_return              NUMERIC,
    settled_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
    PRIMARY KEY (race_id, model_version_id)
);

CREATE TABLE IF NOT EXISTS metric_snapshot (
    id              BIGSERIAL PRIMARY KEY,
    metric_key      TEXT NOT NULL,
    computed_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    numerator       NUMERIC,
    denominator     NUMERIC,
    value           NUMERIC,
    definition      TEXT NOT NULL,
    exclusions      JSONB,
    sample_start    DATE,
    sample_end      DATE,
    dataset_version TEXT NOT NULL
);

-- --------------------------------------------------------------- AUDIT --
CREATE TABLE IF NOT EXISTS correction_ledger (
    id              BIGSERIAL PRIMARY KEY,
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    run_id          TEXT NOT NULL,
    table_name      TEXT NOT NULL,
    record_id       TEXT NOT NULL,
    action          TEXT NOT NULL,                  -- CLASSIFIED / EXCLUDED / RETIRED / RECONSTRUCTED_LOCK / ...
    before_state    JSONB,
    after_state     JSONB,
    reason          TEXT NOT NULL,
    actor           TEXT NOT NULL DEFAULT 'integrity-migration'
);

-- Integrity alerts raised by the gate and health checks (append-only).
CREATE TABLE IF NOT EXISTS integrity_alert (
    id              BIGSERIAL PRIMARY KEY,
    raised_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    alert_type      TEXT NOT NULL,
    severity        TEXT NOT NULL CHECK (severity IN ('INFO', 'WARN', 'CRITICAL')),
    race_id         INT,
    message         TEXT NOT NULL,
    detail          JSONB
);

-- --------------------------------------------------------- TRIGGERS --
DO $$
DECLARE t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY['race_feed_snapshot', 'prediction_lock', 'market_price_snapshot',
                             'race_validation', 'correction_ledger', 'canonical_race_time_history',
                             'integrity_alert']
    LOOP
        EXECUTE format('DROP TRIGGER IF EXISTS trg_append_only ON %I', t);
        EXECUTE format('CREATE TRIGGER trg_append_only BEFORE UPDATE OR DELETE ON %I '
                       'FOR EACH ROW EXECUTE FUNCTION integrity_append_only()', t);
    END LOOP;
END $$;

-- canonical_race: identity columns are immutable, mutable metadata is not.
CREATE OR REPLACE FUNCTION canonical_race_identity_guard() RETURNS trigger AS $$
BEGIN
    IF NEW.canonical_race_id IS DISTINCT FROM OLD.canonical_race_id
       OR NEW.provider_race_id IS DISTINCT FROM OLD.provider_race_id
       OR NEW.meeting_id IS DISTINCT FROM OLD.meeting_id
       OR NEW.race_date IS DISTINCT FROM OLD.race_date
       OR NEW.course_id IS DISTINCT FROM OLD.course_id
       OR NEW.id_basis IS DISTINCT FROM OLD.id_basis
       OR (OLD.race_row_id IS NOT NULL AND NEW.race_row_id IS DISTINCT FROM OLD.race_row_id) THEN
        RAISE EXCEPTION 'canonical_race % identity is immutable (only scheduled time, status and last-seen metadata may change)',
            OLD.canonical_race_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
DROP TRIGGER IF EXISTS trg_canonical_identity_guard ON canonical_race;
CREATE TRIGGER trg_canonical_identity_guard BEFORE UPDATE ON canonical_race
    FOR EACH ROW EXECUTE FUNCTION canonical_race_identity_guard();

-- ------------------------------------------------- PRICE OBSERVATIONS --
-- Legacy market_snapshot (175k live Smarkets rows, never UPDATEd/DELETEd by
-- any code) stays the primary store; it is made append-only here. The new
-- market_price_snapshot holds explicit NULL/reason rows and approved-source
-- fallback rows. One view presents both so readers have a single source.
DROP TRIGGER IF EXISTS trg_append_only ON market_snapshot;
CREATE TRIGGER trg_append_only BEFORE UPDATE OR DELETE ON market_snapshot
    FOR EACH ROW EXECUTE FUNCTION integrity_append_only();

CREATE OR REPLACE VIEW price_observation AS
    SELECT race_id, horse_id, 'smarkets'::text AS source_name, 'EXCHANGE'::text AS source_type,
           FALSE AS is_fallback, exchange_back AS back_price, exchange_lay AS lay_price,
           NULL::numeric AS available_volume, observed_at AS captured_at, price_quality,
           NULL::text AS null_reason, 'legacy:' || id AS ref
    FROM market_snapshot
    UNION ALL
    SELECT race_id, horse_id, source_name, source_type, is_fallback, back_price, lay_price,
           available_volume, captured_at, 'ok'::text AS price_quality, null_reason, 'mps:' || id
    FROM market_price_snapshot;

-- Scheduled off as a UTC instant (race.off_time is a naive UK wall-clock time).
CREATE OR REPLACE FUNCTION race_off_utc(d date, t time) RETURNS timestamptz AS $$
    SELECT ((d + t)::timestamp AT TIME ZONE 'Europe/London')
$$ LANGUAGE sql STABLE;

-- Provider re-issued the race id for the SAME race (same meeting, same time slot, same runners):
-- the new id becomes an alias of the existing canonical race, never a second race.
CREATE TABLE IF NOT EXISTS canonical_race_alias (
    provider_race_id    TEXT PRIMARY KEY,
    canonical_race_id   TEXT NOT NULL REFERENCES canonical_race(canonical_race_id),
    observed_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    reason              TEXT NOT NULL
);
DROP TRIGGER IF EXISTS trg_append_only ON canonical_race_alias;
CREATE TRIGGER trg_append_only BEFORE UPDATE OR DELETE ON canonical_race_alias
    FOR EACH ROW EXECUTE FUNCTION integrity_append_only();
