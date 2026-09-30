-- Silent Edge Zero — canonical schema
-- Every table that reflects "what we knew and when" carries observed_at,
-- available_at, ingested_at, source — this is the leakage-prevention backbone
-- (build brief Section 6). Never drop these columns to "simplify" a table.

CREATE TABLE IF NOT EXISTS data_source (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE,      -- e.g. 'open-meteo', 'theracingapi', 'betfair-exchange'
    url             TEXT,
    free_tier       BOOLEAN NOT NULL DEFAULT TRUE,
    terms_checked   DATE,
    notes           TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS course (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE,
    country         TEXT NOT NULL DEFAULT 'GB',
    latitude        DOUBLE PRECISION,
    longitude       DOUBLE PRECISION
);

-- **Real, known, DELIBERATELY UNFIXED bug, found 2026-09-11 — read before
-- touching this table.** `UNIQUE (name, foaled_year)` below has never
-- actually deduplicated anything: our real data source (The Racing API
-- free tier) never populates foaled_year, it's always NULL, and Postgres
-- treats NULL as distinct from NULL for uniqueness — so every
-- `ON CONFLICT (name, foaled_year)` re-insert of an already-known horse
-- silently created a brand-new duplicate row instead of matching the
-- existing one. Confirmed live: 536 real duplicate horse names, 1,085
-- excess rows — discovered when a duplicate broke real Smarkets price
-- matching for every Doncaster runner (2026-09-11).
--
-- The real, structural fix (two partial unique indexes — see this
-- table's git history for the exact statements) was drafted and reverted
-- the same day: creating it requires the table to already be free of
-- duplicates, and 294 of the 536 duplicate groups are referenced by
-- LOCKED rows in `prediction` — fixing those means deliberately
-- repointing an immutable ledger row's horse_id (with a proper
-- trigger-disable, re-hash, and real testing), which needs Jonathan's
-- explicit go-ahead before being done at scale, not a silent migration.
-- Until that happens: `scripts/collect_smarkets_prices.py::load_our_races`
-- was changed to source horse_id via `prediction` (the real, single
-- source of truth everything else already depends on) instead of raw
-- `runner_snapshot`, which fixes the actual user-visible symptom (a
-- newer duplicate horse row silently breaking Smarkets price matching)
-- without needing this migration — see that function's own docstring.
CREATE TABLE IF NOT EXISTS horse (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,
    foaled_year     INT,
    sex             TEXT,
    external_ref    TEXT,               -- provider's own horse id, for dedup on re-ingest
    source_id       INT REFERENCES data_source(id),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (name, foaled_year)
);

CREATE TABLE IF NOT EXISTS trainer (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE,
    external_ref    TEXT
);

CREATE TABLE IF NOT EXISTS jockey (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE,
    external_ref    TEXT
);

-- A "race" record itself is filled in progressively (racecard first, result
-- fields after) — but the PRE_RACE_SNAPSHOT/POST_RACE_RESULT split (build
-- brief Section 5) lives in runner_snapshot / runner_result below, not here,
-- so a re-fetched racecard never silently overwrites what we knew pre-race.
CREATE TABLE IF NOT EXISTS race (
    id              SERIAL PRIMARY KEY,
    course_id       INT NOT NULL REFERENCES course(id),
    race_date       DATE NOT NULL,
    off_time        TIME NOT NULL,
    race_name       TEXT,
    race_class      TEXT,
    race_type       TEXT,               -- Flat Turf / AW / Hurdle / Chase / NH Flat
    distance_yards  INT,
    surface         TEXT,
    going           TEXT,               -- as known at ingest time; going can change, see going_update
    field_size      INT,
    prize_money     NUMERIC,
    external_ref    TEXT,
    source_id       INT REFERENCES data_source(id),
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (course_id, race_date, off_time)
);

-- Going changes through the day — never overwrite race.going in place once a
-- prediction may have used it. Append updates instead.
CREATE TABLE IF NOT EXISTS going_update (
    id              SERIAL PRIMARY KEY,
    race_id         INT NOT NULL REFERENCES race(id),
    going           TEXT NOT NULL,
    observed_at     TIMESTAMPTZ NOT NULL,
    available_at    TIMESTAMPTZ NOT NULL,
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_id       INT REFERENCES data_source(id)
);

-- PRE_RACE_SNAPSHOT: everything known about a runner before the race.
-- Immutable once written — a re-ingest creates a NEW row with a later
-- ingested_at, never an UPDATE. This is what "never overwrite the pre-race
-- snapshot" (Section 5) means in schema terms.
CREATE TABLE IF NOT EXISTS runner_snapshot (
    id                  SERIAL PRIMARY KEY,
    race_id             INT NOT NULL REFERENCES race(id),
    horse_id            INT NOT NULL REFERENCES horse(id),
    trainer_id          INT REFERENCES trainer(id),
    jockey_id           INT REFERENCES jockey(id),
    age                 INT,
    draw                INT,
    weight_lbs          INT,
    official_rating     INT,
    recent_form         TEXT,           -- e.g. '1-3-6-2'
    days_since_last_run INT,
    equipment           TEXT,
    non_runner          BOOLEAN NOT NULL DEFAULT FALSE,
    observed_at         TIMESTAMPTZ NOT NULL,   -- when this info was true
    available_at        TIMESTAMPTZ NOT NULL,   -- when we could have known it (leakage guard)
    ingested_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_id           INT REFERENCES data_source(id)
);

-- POST_RACE_RESULT: kept fully separate from runner_snapshot.
CREATE TABLE IF NOT EXISTS runner_result (
    id                  SERIAL PRIMARY KEY,
    race_id             INT NOT NULL REFERENCES race(id),
    horse_id            INT NOT NULL REFERENCES horse(id),
    finishing_position  INT,            -- NULL if non-runner/pulled up/etc, see result_note
    distance_beaten     NUMERIC,
    starting_price      NUMERIC,
    bsp                 NUMERIC,        -- Betfair Starting Price, when available
    result_note         TEXT,           -- 'PU', 'F', 'NR', etc.
    observed_at         TIMESTAMPTZ NOT NULL,
    available_at        TIMESTAMPTZ NOT NULL,
    ingested_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_id           INT REFERENCES data_source(id),
    UNIQUE (race_id, horse_id)
);

-- One real row per race_date, computed by scripts/generate_daily_summary.py
-- once runner_result has real settled outcomes for that day. Re-runnable
-- (UPSERT) as more results land through the day/evening — never a
-- fabricated or estimated row; races still pending are simply excluded
-- from that day's counts, not guessed. This is the persisted history that
-- backs the dashboard's "track record" chart, so a single day's numbers
-- survive past that day and accumulate into a real long-run answer to
-- "how good is this app, really".
CREATE TABLE IF NOT EXISTS daily_summary (
    race_date              DATE PRIMARY KEY,
    races_total             INT NOT NULL,
    races_settled            INT NOT NULL,
    top_pick_wins             INT NOT NULL,
    top_pick_placed            INT NOT NULL,   -- within real EW place terms for that race's field size
    favourite_wins             INT NOT NULL,   -- real market favourite (lowest exchange_back), for comparison
    win_stake_total            NUMERIC NOT NULL,   -- total real £1-per-race stake actually settled
    win_profit                 NUMERIC NOT NULL,
    ew_stake_total              NUMERIC NOT NULL,  -- total real £2-per-race stake actually settled
    ew_profit                   NUMERIC NOT NULL,
    sp_priced_races             INTEGER NOT NULL DEFAULT 0,  -- races settled on starting price because no exchange price was captured
    computed_at                 TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Market snapshots — captured at whatever cadence is actually achievable on
-- free access (Section 15 lists an ideal T-60/T-30/... schedule; free tiers
-- may not support all of it — store whatever we legitimately get).
CREATE TABLE IF NOT EXISTS market_snapshot (
    id                  SERIAL PRIMARY KEY,
    race_id             INT NOT NULL REFERENCES race(id),
    horse_id            INT NOT NULL REFERENCES horse(id),
    bookmaker_odds      NUMERIC,        -- decimal odds
    exchange_back       NUMERIC,
    exchange_lay        NUMERIC,
    midprice            NUMERIC,
    spread              NUMERIC,
    observed_at         TIMESTAMPTZ NOT NULL,
    available_at        TIMESTAMPTZ NOT NULL,
    ingested_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_id           INT REFERENCES data_source(id)
);

-- Research V2 brief, Phase 1: real price-quality flag, added after a live
-- 2026-09-18 finding — a Smarkets back price of 10000.0 (a near-worthless
-- stub bid with no real liquidity) was being treated identically to a
-- genuine market price, producing a nonsensical "BEST VALUE, EV +1954%"
-- display. 'ok' / 'thin_book' / 'wide_spread', set by
-- scripts/collect_smarkets_prices.py at insert time — see that script and
-- src/providers/odds_smarkets.py for the real classification rule.
-- Existing rows default to 'ok': they predate this check and were not
-- re-evaluated retroactively (never invent a quality judgement for data we
-- didn't actually check).
ALTER TABLE market_snapshot ADD COLUMN IF NOT EXISTS price_quality TEXT NOT NULL DEFAULT 'ok';

-- Research V2 brief, Phase 5/6 (Sections 12B, 14): real historical
-- multi-point Betfair price data from the Kaggle betfair_mapping CSVs
-- (data/kaggle_historical/betfair/), previously loaded into the repo but
-- never imported. Only covers 2026-03-01 to 2026-04-29 (confirmed via the
-- CSVs themselves — the dataset's own README claim of broader coverage
-- does not hold for this file), worldwide courses (filtered to GB at
-- import time by scripts/load_kaggle_betfair_historical.py). A genuinely
-- separate table from `market_snapshot` (which is a live, point-in-time
-- order-book time series) because this source's own fields have
-- different real semantics — morning/pre-off/in-play RANGES, not
-- individual timestamped snapshots.
--
-- LEAKAGE WARNING, real and load-bearing: ip_min/ip_max are IN-PLAY prices
-- — recorded strictly AFTER the race started. They must never be used as
-- an input to any pre-race feature or historical simulated forecast
-- (brief Section 12B: "never use later prices as inputs to an earlier
-- simulated forecast"). Only sp, bsp, wap, morning_wap, pre_min, pre_max
-- are genuinely pre-race-knowable.
CREATE TABLE IF NOT EXISTS historical_betfair_price (
    id              SERIAL PRIMARY KEY,
    race_id         INT NOT NULL REFERENCES race(id),
    horse_id        INT NOT NULL REFERENCES horse(id),
    starting_price  NUMERIC,        -- decimal SP, converted from the CSV's fractional string
    bsp             NUMERIC,        -- Betfair Starting Price
    wap             NUMERIC,        -- volume-weighted average price, whole market
    morning_wap     NUMERIC,        -- pre-race-knowable
    pre_min         NUMERIC,        -- pre-race-knowable
    pre_max         NUMERIC,        -- pre-race-knowable
    ip_min          NUMERIC,        -- IN-PLAY — post-off, never pre-race-knowable, see warning above
    ip_max          NUMERIC,        -- IN-PLAY — post-off, never pre-race-knowable, see warning above
    morning_vol     NUMERIC,
    pre_vol         NUMERIC,
    ip_vol          NUMERIC,
    source_id       INT REFERENCES data_source(id),
    ingested_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (race_id, horse_id)
);

-- Weather snapshot per course per day — feature input, not a race-specific record.
CREATE TABLE IF NOT EXISTS weather_snapshot (
    id                  SERIAL PRIMARY KEY,
    course_id           INT NOT NULL REFERENCES course(id),
    for_date            DATE NOT NULL,
    rainfall_6h_mm      NUMERIC,
    rainfall_24h_mm     NUMERIC,
    temperature_c       NUMERIC,
    wind_speed_kmh      NUMERIC,
    wind_direction_deg  NUMERIC,
    observed_at         TIMESTAMPTZ NOT NULL,
    available_at        TIMESTAMPTZ NOT NULL,
    ingested_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
    source_id           INT REFERENCES data_source(id)
);

-- Model versioning (Section 9: "never retrospectively change an old
-- prediction when the rating methodology changes" — every prediction is
-- tagged with the model/feature version that produced it).
CREATE TABLE IF NOT EXISTS model_version (
    id              SERIAL PRIMARY KEY,
    name            TEXT NOT NULL,          -- 'market_baseline', 'statistical_v1', 'gbm_v1', 'ensemble_v1'
    version         TEXT NOT NULL,
    feature_version TEXT,
    description     TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (name, version)
);

-- Immutable prediction ledger (Section 32). No UPDATE path should ever be
-- used on a locked row — application code enforces "insert new row, never
-- update" once locked_at is set.
CREATE TABLE IF NOT EXISTS prediction (
    id                  SERIAL PRIMARY KEY,
    race_id             INT NOT NULL REFERENCES race(id),
    horse_id            INT NOT NULL REFERENCES horse(id),
    model_version_id    INT NOT NULL REFERENCES model_version(id),
    model_probability   NUMERIC NOT NULL,
    market_probability  NUMERIC,
    fair_odds           NUMERIC,
    available_odds      NUMERIC,
    absolute_edge       NUMERIC,
    relative_edge       NUMERIC,
    expected_value      NUMERIC,
    model_confidence    TEXT,           -- LOW/MODERATE/HIGH — not a precise number, see Section 26
    data_confidence     TEXT,
    signal              TEXT,           -- A+/A/B/C/WATCH/PASS — all UNVALIDATED until evidenced, Section 28
    locked_at           TIMESTAMPTZ,    -- once set, this row is immutable
    record_hash         TEXT,           -- SHA-256 of the locked record, Section 32
    created_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_runner_snapshot_race ON runner_snapshot(race_id);
CREATE INDEX IF NOT EXISTS idx_runner_result_race ON runner_result(race_id);
CREATE INDEX IF NOT EXISTS idx_market_snapshot_race_horse ON market_snapshot(race_id, horse_id);
CREATE INDEX IF NOT EXISTS idx_prediction_race ON prediction(race_id);
CREATE INDEX IF NOT EXISTS idx_race_date ON race(race_date);

-- Prediction immutability, enforced by the database, not just application
-- discipline (Section 32). Once locked_at is set on a row, ANY update to
-- that row is rejected outright -- the only legitimate way to change a
-- prediction after that point is to INSERT a new row under a new
-- model_version. A row that hasn't been locked yet (locked_at IS NULL) can
-- still be updated freely, e.g. to set locked_at itself at lock time.
-- CREATE OR REPLACE + DROP TRIGGER IF EXISTS makes this block safe to
-- re-run, same as every CREATE TABLE IF NOT EXISTS above.
CREATE OR REPLACE FUNCTION prevent_locked_prediction_update() RETURNS trigger AS $$
BEGIN
    IF OLD.locked_at IS NOT NULL THEN
        RAISE EXCEPTION
            'prediction % is locked (locked_at=%) and is immutable -- insert a new prediction row under a new model_version instead of updating it',
            OLD.id, OLD.locked_at;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_prevent_locked_prediction_update ON prediction;
CREATE TRIGGER trg_prevent_locked_prediction_update
    BEFORE UPDATE ON prediction
    FOR EACH ROW
    EXECUTE FUNCTION prevent_locked_prediction_update();
