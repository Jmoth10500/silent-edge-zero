"""Central metrics layer: ONE place that defines every public number.

Every metric exposes numerator, denominator, definition, exclusions, sample
dates, refresh time and the dataset version. Dashboards must read from here;
`reconcile()` proves the population identities hold exactly.

Population tree (gbm_v1 locked top pick, one bet per race):
  RAW predicted races
   = VALID (include_in_metrics)  +  EXCLUDED (INVALID_DUPLICATE / INVALID_RACE_ID / OTHER)
  VALID = SETTLED (top pick status known) + PENDING (no result yet / missing result)
  SETTLED = GENUINE_RUNNER (top pick ran) + VOID (top pick non-runner / void race)
  GENUINE_RUNNER = STAKED (has a price) + UNSTAKED (no price at all)
  STAKED = EXCHANGE_LOCK + EXCHANGE_OTHER + SP
"""
import hashlib
import json
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

from src.integrity.canonical import horse_key, meeting_id
from src.integrity.classify import Classification, RaceFacts, classify_races
from src.integrity.market import Quote, choose_bet_price, lock_market_state
from src.integrity.settlement import (
    PriceType, ResultStatus, classify_result, is_genuine_runner, is_settled, settle_win_bet,
)

LONDON = ZoneInfo("Europe/London")
MODEL = "gbm_v1"
STAKE = 1.0
EW_PLACES_LOOKUP = None        # win-only metrics: PLACED vs FINISHED_UNPLACED split not needed here


def off_datetime(race_date: date, off_time) -> datetime:
    return datetime.combine(race_date, off_time).replace(tzinfo=LONDON).astimezone(timezone.utc)


@dataclass
class RaceRecord:
    facts: RaceFacts
    off_dt: datetime
    top_horse_id: int
    top_horse_name: str
    top_prob: float
    top_position: Optional[int]
    top_note: Optional[str]
    top_sp: Optional[float]
    quotes: list
    model_version_id: int
    field: list = field(default_factory=list)   # [dict(horse_id, name, prob, pos, note, sp, quotes)] full predicted field


@dataclass
class Dataset:
    records: list
    classifications: dict
    today: date
    loaded_at: datetime

    @property
    def version(self) -> str:
        h = hashlib.sha256()
        for r in self.records:
            c = self.classifications[r.facts.race_id]
            h.update(f"{r.facts.race_id}|{c.classification}|{r.top_position}|{r.top_note}|{len(r.quotes)}".encode())
        return h.hexdigest()[:16]


def load_dataset(conn, since: date = date(2026, 9, 1), today: Optional[date] = None) -> Dataset:
    today = today or date.today()
    cur = conn.cursor()
    cur.execute(
        """SELECT r.id, r.race_date, c.name, r.off_time, r.external_ref, r.race_name,
                  h.id, h.name, p.model_probability, p.model_version_id,
                  rr.finishing_position, rr.result_note, rr.starting_price
           FROM prediction p
           JOIN model_version mv ON mv.id = p.model_version_id AND mv.name = %s
           JOIN race r ON r.id = p.race_id JOIN course c ON c.id = r.course_id
           JOIN horse h ON h.id = p.horse_id
           LEFT JOIN runner_result rr ON rr.race_id = r.id AND rr.horse_id = p.horse_id
           WHERE p.locked_at IS NOT NULL AND r.race_date >= %s""", (MODEL, since))
    races: dict = {}
    for (rid, rdate, course, off, ref, name, hid, hname, prob, mvid, pos, note, sp) in cur.fetchall():
        e = races.setdefault(rid, dict(rdate=rdate, course=course, off=off, ref=ref, name=name, mv=mvid, runners=[]))
        if mvid != e["mv"]:
            continue                       # a race scored under two versions: keep the first-seen version only
        e["runners"].append((float(prob), hid, hname, pos, note, float(sp) if sp is not None else None))

    ids = list(races)
    results: dict = {i: [] for i in ids}
    cur.execute("SELECT race_id, finishing_position, result_note FROM runner_result WHERE race_id = ANY(%s)", (ids,))
    for rid, pos, note in cur.fetchall():
        results[rid].append((pos, note))
    quotes: dict = {i: {} for i in ids}
    cur.execute("""SELECT race_id, horse_id, back_price, lay_price, captured_at, source_name, source_type,
                          is_fallback, price_quality FROM price_observation WHERE race_id = ANY(%s)""", (ids,))
    for rid, hid, back, lay, at, sname, stype, fb, pq in cur.fetchall():
        quotes[rid].setdefault(hid, []).append(Quote(
            float(back) if back is not None else None, float(lay) if lay is not None else None,
            at, sname, stype, fb, pq))
    cur.close()

    records, facts = [], []
    for rid, e in races.items():
        top = max(e["runners"], key=lambda x: x[0])
        off_dt = off_datetime(e["rdate"], e["off"])
        q = quotes[rid].get(top[1], [])
        f = RaceFacts(
            race_id=rid, race_date=e["rdate"], meeting=meeting_id(e["rdate"], e["course"]), off_time=str(e["off"]),
            provider_race_id=e["ref"], race_name=e["name"] or "",
            pred_keys=frozenset(horse_key(x[2]) for x in e["runners"]), result_notes=results[rid],
            lock_market_state=lock_market_state(q, off_dt))
        facts.append(f)
        fld = [dict(horse_id=x[1], name=x[2], prob=x[0], pos=x[3], note=x[4], sp=x[5],
                    quotes=quotes[rid].get(x[1], [])) for x in sorted(e["runners"], key=lambda t: -t[0])]
        records.append(RaceRecord(f, off_dt, top[1], top[2], top[0], top[3], top[4], top[5], q, e["mv"], fld))
    return Dataset(records, classify_races(facts, today), today, datetime.now(timezone.utc))


def settle_record(rec: RaceRecord, commission_rate: float = 0.0):
    """-> (Settlement, PriceChoice) for the top-pick £1 win bet."""
    status = classify_result(rec.top_position, rec.top_note)
    choice = choose_bet_price(rec.quotes, rec.off_dt, rec.top_sp)
    return settle_win_bet(STAKE, choice.price, choice.price_type, status, commission_rate), choice


@dataclass
class Metric:
    key: str
    numerator: Optional[float]
    denominator: Optional[float]
    definition: str
    exclusions: dict = field(default_factory=dict)
    sample_start: Optional[date] = None
    sample_end: Optional[date] = None

    @property
    def value(self) -> Optional[float]:
        if self.denominator in (None, 0) or self.numerator is None:
            return None
        return self.numerator / self.denominator


def compute(ds: Dataset) -> dict:
    cls = ds.classifications
    valid = [r for r in ds.records if cls[r.facts.race_id].include_in_metrics]
    excluded = [r for r in ds.records if not cls[r.facts.race_id].include_in_metrics]
    exc_reasons: dict = {}
    for r in excluded:
        exc_reasons[cls[r.facts.race_id].classification] = exc_reasons.get(cls[r.facts.race_id].classification, 0) + 1

    settled, pending, void, genuine = [], [], [], []
    price_groups: dict = {t: [] for t in PriceType}
    for r in valid:
        st, ch = settle_record(r)
        status = st.status
        if not is_settled(status):
            pending.append(r)
            continue
        settled.append((r, st, ch))
        if is_genuine_runner(status):
            genuine.append((r, st, ch))
            price_groups[ch.price_type].append((r, st, ch))
        else:
            void.append(r)

    def pnl(rows):
        staked = [(r, st) for r, st, ch in rows if st.settled and st.net_return is not None and st.price is not None]
        n = len(staked)
        profit = sum(st.net_return for _, st in staked)
        wins = sum(1 for _, st in staked if st.status == ResultStatus.WIN)
        return n, profit, wins

    lock_rows = price_groups[PriceType.EXCHANGE_LOCK]
    oth_rows = price_groups[PriceType.EXCHANGE_OTHER]
    sp_rows = price_groups[PriceType.SP]
    mixed_rows = lock_rows + oth_rows + sp_rows

    def sample(rows):
        ds_ = [r.facts.race_date for r in rows]
        return (min(ds_), max(ds_)) if ds_ else (None, None)

    all_dates = sample(valid)
    wins_all = sum(1 for r, st, ch in genuine if st.status == ResultStatus.WIN)
    m = {}
    m["raw_predicted_races"] = Metric("raw_predicted_races", len(ds.records), None,
        f"distinct races with a locked {MODEL} prediction since 2026-09-01 (before any exclusion)",
        sample_start=sample(ds.records)[0], sample_end=sample(ds.records)[1])
    m["valid_races"] = Metric("valid_races", len(valid), len(ds.records),
        "raw predicted races whose integrity classification has include_in_metrics=TRUE",
        exclusions=exc_reasons, sample_start=all_dates[0], sample_end=all_dates[1])
    m["excluded_races"] = Metric("excluded_races", len(excluded), len(ds.records),
        "INVALID_DUPLICATE (superseded provisional card), INVALID_RACE_ID (shared provider id), OTHER (locked on non-final field)",
        exclusions=exc_reasons)
    m["settled_races"] = Metric("settled_races", len(settled), len(valid),
        "valid races whose top pick has a known outcome (ran, or void/non-runner)",
        sample_start=sample([r for r, _, _ in settled])[0], sample_end=sample([r for r, _, _ in settled])[1])
    m["pending_races"] = Metric("pending_races", len(pending), len(valid),
        "valid races with no result yet (future/today) or MISSING_RESULT (past date, nothing collected)",
        exclusions={"missing_result_past": sum(1 for r in pending if cls[r.facts.race_id].classification == "MISSING_RESULT")})
    m["void_races"] = Metric("void_races", len(void), len(settled),
        "settled races where the top pick was a non-runner or the race was void (stake refunded; not a loss)")
    m["genuine_runner_races"] = Metric("genuine_runner_races", len(genuine), len(settled),
        "settled races where the top pick actually ran (win, finish, or F/PU/UR/etc.)")
    m["top_pick_win_rate"] = Metric("top_pick_win_rate", wins_all, len(genuine),
        "top-pick wins / genuine-runner top picks (F/PU/UR/BD/RR/RO/DSQ/SU/REF/CO/U count as LOSSES, void/NR excluded)",
        exclusions={"void_or_nr": len(void), "pending": len(pending), "excluded_invalid": len(excluded)},
        sample_start=sample([r for r, _, _ in genuine])[0], sample_end=sample([r for r, _, _ in genuine])[1])
    for key, label, rows, defn in (
        ("pnl_exchange_lock", "A", lock_rows, "£1 win on top pick at the last valid exchange price in [off-30m, off-60s]; EXCHANGE-ONLY, executable"),
        ("pnl_exchange_other", "A2", oth_rows, "£1 win at a valid pre-off exchange price OUTSIDE the lock window (earlier in the day); exchange but not lock-time"),
        ("pnl_sp", "B", sp_rows, "£1 win at Starting Price because no pre-off exchange price exists; bookmaker-style SP, NOT executable on the exchange"),
        ("pnl_mixed", "C", mixed_rows, "MIXED / NON-HOMOGENEOUS: exchange-lock + exchange-other + SP combined. Not equivalent to executable exchange ROI."),
    ):
        n, profit, wins = pnl(rows)
        s, e = sample([r for r, _, _ in rows])
        m[key] = Metric(key, profit, n, f"[{label}] {defn}. numerator = net £ profit, denominator = £ staked (n bets × £1)",
                        exclusions={"wins": wins}, sample_start=s, sample_end=e)
    m["unstaked_genuine"] = Metric("unstaked_genuine", len(price_groups[PriceType.NO_PRICE]), len(genuine),
        "genuine-runner races with no exchange AND no SP price (NO_PRICE): excluded from every ROI")
    m["lock_market_coverage"] = Metric("lock_market_coverage",
        sum(1 for r in valid if r.facts.lock_market_state == "LOCK_VALID" and r.facts.race_date < ds.today), 
        sum(1 for r in valid if r.facts.race_date < ds.today),
        "past valid races with a valid lock-window exchange snapshot for the top pick / past valid races")
    return {"metrics": m, "settled": settled, "pending": pending, "void": void, "genuine": genuine,
            "valid": valid, "excluded": excluded, "price_groups": price_groups}


def reconcile(ds: Dataset, c: Optional[dict] = None) -> list:
    """Population identities. Returns [(name, lhs, rhs, ok)]. All must hold exactly."""
    c = c or compute(ds)
    m = c["metrics"]
    pg = c["price_groups"]
    checks = [
        ("raw = valid + excluded", len(ds.records), len(c["valid"]) + len(c["excluded"])),
        ("valid = settled + pending", len(c["valid"]), len(c["settled"]) + len(c["pending"])),
        ("settled = genuine_runner + void", len(c["settled"]), len(c["genuine"]) + len(c["void"])),
        ("genuine_runner = exchange_lock + exchange_other + sp + no_price", len(c["genuine"]),
         sum(len(pg[t]) for t in PriceType)),
        ("staked(mixed) = lock + other + sp", int(m["pnl_mixed"].denominator),
         int(m["pnl_exchange_lock"].denominator + m["pnl_exchange_other"].denominator + m["pnl_sp"].denominator)),
        ("win_rate numerator <= denominator", 1, 1 if m["top_pick_win_rate"].numerator <= m["top_pick_win_rate"].denominator else 0),
        ("no orphans: every raw race classified", len(ds.records), len(ds.classifications)),
    ]
    return [(n, a, b, a == b) for n, a, b in checks]


def persist(conn, ds: Dataset, c: dict, run_id: str):
    """Write bet_settlement (derived, re-computable) and a metric_snapshot row per metric."""
    cur = conn.cursor()
    for r, st, ch in c["settled"]:
        cur.execute(
            """INSERT INTO bet_settlement (race_id, model_version_id, horse_id, settlement_price, settlement_price_type,
                   price_timestamp, price_source, result_status, stake, gross_return, commission, net_return)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
               ON CONFLICT (race_id, model_version_id) DO UPDATE SET
                   horse_id=EXCLUDED.horse_id, settlement_price=EXCLUDED.settlement_price,
                   settlement_price_type=EXCLUDED.settlement_price_type, price_timestamp=EXCLUDED.price_timestamp,
                   price_source=EXCLUDED.price_source, result_status=EXCLUDED.result_status, stake=EXCLUDED.stake,
                   gross_return=EXCLUDED.gross_return, commission=EXCLUDED.commission, net_return=EXCLUDED.net_return,
                   settled_at=now()""",
            (r.facts.race_id, r.model_version_id, r.top_horse_id, st.price, st.price_type.value,
             ch.captured_at, ch.source, st.status.value, st.stake, st.gross_return, st.commission, st.net_return))
    for m in c["metrics"].values():
        cur.execute(
            """INSERT INTO metric_snapshot (metric_key, numerator, denominator, value, definition, exclusions,
                   sample_start, sample_end, dataset_version) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
            (m.key, m.numerator, m.denominator, m.value, m.definition, json.dumps(m.exclusions),
             m.sample_start, m.sample_end, ds.version))
    conn.commit()
