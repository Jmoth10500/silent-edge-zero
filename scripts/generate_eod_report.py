#!/usr/bin/env python3
"""
End-of-day report — top picks, the market favourite, and what a real £1
win / £2 each-way stake on each top pick would have returned.

Built per Jonathan's real request (2026-09-10): "tell me what the top picks
were of the day and if they won or placed... if I were to put £1 on each
top pick... £2 E/W each top pick... who the favourite was and where it
placed."

**Real, honest limitation, checked live before writing a line of this
script:** `runner_result` has no rows for any live race day — only the
2026-05-27-and-earlier Kaggle historical bootstrap. Confirmed via direct
query against `silent_edge_zero` on 2026-09-10 (see docs/BUILD_LOG.md,
"Racing API's own results — still needs their Basic tier", unresolved).
This script is therefore built to run correctly the moment real result
rows exist for a date, and until then reports every outcome/P&L field as
PENDING rather than guessing or inventing a result — never silently
treats a missing result as a loss or a win.

**Top pick** = the single highest `model_probability` runner from the
primary model (gbm_v1 / "Model 2", per docs/BUILD_LOG.md's dashboard
work) for each race, restricted to locked predictions only.

**Favourite** = the runner with the lowest real `exchange_back` price
(most recent Smarkets snapshot per horse) in the race. A race with no
real market_snapshot rows for any runner has no favourite reported
(never guessed from the model's own probability instead — that would
silently misrepresent a model output as a market fact).

**Each-way terms**, since none are stored anywhere in this DB and real
terms vary by bookmaker and race type: this report uses the common
simplified default (2-4 runners win-only, 5-7 runners 1/4 odds 2 places,
8+ runners 1/5 odds 3 places) and prints that assumption on every run —
never hides it. Field size = count of distinct horses with a locked
gbm_v1 prediction in that race.

Usage: python3 scripts/generate_eod_report.py [race_date]
Defaults to today.
"""
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

EW_TERMS = [
    (5, "Win only (2-4 runners)", None, 0),
    (8, "1/4 odds, 2 places (5-7 runners)", 0.25, 2),
    (12, "1/5 odds, 3 places (8-11 runners)", 0.2, 3),
    (16, "1/4 odds, 3 places (12-15 runners)", 0.25, 3),
    (999, "1/4 odds, 4 places (16+ runners)", 0.25, 4),
]


def ew_terms_for_field_size(field_size: int):
    """Returns (label, place_fraction_or_None, n_places) for a given field size.
    Simplified industry-standard default — see module docstring."""
    for upper, label, frac, places in EW_TERMS:
        if field_size < upper:
            return label, frac, places
    return EW_TERMS[-1][1], EW_TERMS[-1][2], EW_TERMS[-1][3]


def load_top_picks_and_favourites(conn, race_date: date):
    cur = conn.cursor()
    cur.execute(
        """
        SELECT r.id, r.off_time, c.name, r.race_name, h.id, h.name,
               p.model_probability, ms.exchange_back, rr.starting_price
        FROM prediction p
        JOIN race r ON r.id = p.race_id
        JOIN course c ON c.id = r.course_id
        JOIN horse h ON h.id = p.horse_id
        JOIN model_version mv ON mv.id = p.model_version_id
        LEFT JOIN runner_result rr ON rr.race_id = r.id AND rr.horse_id = h.id
        LEFT JOIN LATERAL (
            SELECT exchange_back
            FROM market_snapshot ms2
            WHERE ms2.race_id = r.id AND ms2.horse_id = p.horse_id
            ORDER BY ms2.observed_at DESC LIMIT 1
        ) ms ON true
        WHERE r.race_date = %s AND p.locked_at IS NOT NULL AND mv.name = 'gbm_v1'
        ORDER BY r.off_time, r.id, p.model_probability DESC
        """,
        (race_date,),
    )
    rows = cur.fetchall()
    cur.close()

    races: dict[int, dict] = {}
    order: list[int] = []
    for (race_id, off_time, course_name, race_name, horse_id, horse_name,
         prob, exchange_back, starting_price) in rows:
        if race_id not in races:
            races[race_id] = {
                "race_id": race_id, "off_time": off_time, "course_name": course_name,
                "race_name": race_name, "runners": [], "field_size": 0,
            }
            order.append(race_id)
        races[race_id]["runners"].append({
            "horse_id": horse_id, "horse_name": horse_name,
            "model_probability": float(prob),
            "exchange_back": float(exchange_back) if exchange_back is not None else None,
            "starting_price": float(starting_price) if starting_price is not None else None,
        })
        races[race_id]["field_size"] += 1

    out = []
    for rid in order:
        race = races[rid]
        runners = race["runners"]
        top_pick = max(runners, key=lambda x: x["model_probability"])
        race["odds_basis"] = "exchange"
        if not any(x["exchange_back"] is not None for x in runners) and any(
                x["starting_price"] is not None for x in runners):
            # No exchange price was ever captured for this race (e.g. the
            # 2026-09-24..30 Smarkets outage). Fall back to the real starting
            # price for the WHOLE race (never mixed within a race) so the race
            # can still be settled. `exchange_back` carries the SP here; the
            # race is flagged odds_basis="sp" so callers can disclose it.
            race["odds_basis"] = "sp"
            for x in runners:
                x["exchange_back"] = x["starting_price"]
        priced = [x for x in runners if x["exchange_back"] is not None]
        favourite = min(priced, key=lambda x: x["exchange_back"]) if priced else None
        race["top_pick"] = top_pick
        race["favourite"] = favourite
        out.append(race)
    return out


def load_results(conn, race_date: date):
    """Real finishing positions for the given date, keyed by (race_id, horse_id).
    Empty dict on a date with no results collected — honest, not an error."""
    cur = conn.cursor()
    cur.execute(
        """
        SELECT rr.race_id, rr.horse_id, rr.finishing_position, rr.result_note
        FROM runner_result rr
        JOIN race r ON r.id = rr.race_id
        WHERE r.race_date = %s
        """,
        (race_date,),
    )
    rows = cur.fetchall()
    cur.close()
    return {(race_id, horse_id): (pos, note) for race_id, horse_id, pos, note in rows}


# Real result_note codes that mean "no bet ever stood" (the horse was
# withdrawn before the race) — stake is void/refunded, not lost. Distinct
# from a real non-finish (PU/F/UR/BD/RR/RO/DSQ/SU/REF/CO/FELL — the horse
# actually ran) which is a genuine loss. Found 2026-09-15 investigating
# Jonathan's "there is 6 pending why?" — 3 of those 6 were real NR top
# picks that this script (and generate_daily_summary.py, which reuses
# these functions) had been silently leaving PENDING forever, since a
# withdrawn horse's finishing_position is NULL for good, never settling.
# See docs/BUILD_LOG.md's 2026-09-15 entry.
VOID_RESULT_CODES = {"NR", "VOID"}


def settle_win(stake: float, odds: float | None, position: int | None,
                result_note: str | None = None):
    """Real settlement for a straight win bet. Returns (profit_or_None, note).
    result_note distinguishes a genuinely pending result (None) from a real
    terminal non-finish (NR/VOID = stake refunded; any other code = the
    horse ran and didn't finish, a real loss) — see VOID_RESULT_CODES."""
    if odds is None:
        return None, "no real price available"
    if position is None:
        if result_note is None:
            return None, "PENDING — result not yet collected"
        if result_note in VOID_RESULT_CODES:
            return 0.0, f"VOID ({result_note}) — non-runner, stake refunded"
        return round(-stake, 2), f"lost — did not finish ({result_note})"
    if position == 1:
        return round(stake * (odds - 1), 2), "WON"
    return round(-stake, 2), "lost"


def settle_each_way(total_stake: float, odds: float | None, position: int | None,
                     field_size: int, result_note: str | None = None):
    """Real each-way settlement: total_stake split evenly win/place (e.g. £2
    total = £1 win + £1 place). Returns (profit_or_None, note). result_note
    as in settle_win — distinguishes real PENDING from a terminal NR/VOID
    (whole stake refunded) or a real non-finish (whole stake lost)."""
    label, frac, n_places = ew_terms_for_field_size(field_size)
    if odds is None:
        return None, f"no real price available ({label})"
    if position is None:
        if result_note is None:
            return None, f"PENDING — result not yet collected ({label})"
        if result_note in VOID_RESULT_CODES:
            return 0.0, f"VOID ({result_note}) — non-runner, stake refunded ({label})"
        return round(-total_stake, 2), f"lost — did not finish ({result_note}) ({label})"
    win_stake = total_stake / 2
    place_stake = total_stake / 2
    if frac is None:  # win-only terms, e.g. small field
        # place_stake still rides, but with no each-way terms it's void back at cost
        win_profit = win_stake * (odds - 1) if position == 1 else -win_stake
        return round(win_profit, 2), f"{label} — place portion void, stake returned"
    win_profit = win_stake * (odds - 1) if position == 1 else -win_stake
    place_odds = 1 + (odds - 1) * frac
    if position is not None and position <= n_places:
        place_profit = place_stake * (place_odds - 1)
    else:
        place_profit = -place_stake
    total_profit = win_profit + place_profit
    outcome = "WON (win+place)" if position == 1 else (
        f"PLACED (pos {position})" if position <= n_places else "lost"
    )
    return round(total_profit, 2), f"{outcome} — {label}"


def main():
    race_date = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()

    conn = psycopg2.connect(dbname="silent_edge_zero")
    races = load_top_picks_and_favourites(conn, race_date)
    results = load_results(conn, race_date)
    conn.close()

    if not races:
        print(f"No locked gbm_v1 predictions found for {race_date}.")
        return

    print(f"\n{'=' * 72}")
    print(f"  END-OF-DAY REPORT — {race_date}  ({len(races)} races)")
    print(f"{'=' * 72}")
    print(
        "  Each-way terms used (not stored anywhere — simplified default,\n"
        "  varies by real bookmaker): 2-4 win-only / 5-7 1/4 odds 2 places /\n"
        "  8-11 1/5 odds 3 places / 12-15 1/4 odds 3 places / 16+ 1/4 odds 4 places."
    )
    have_any_results = bool(results)
    if not have_any_results:
        print(
            "\n  ** No result data exists yet for this date. Every outcome and\n"
            "     P&L line below is PENDING, not a loss — this project does not\n"
            "     have a live results feed connected (see docs/BUILD_LOG.md). **"
        )

    win_total, ew_total = 0.0, 0.0
    win_pending, ew_pending = 0, 0

    for race in races:
        tp = race["top_pick"]
        fav = race["favourite"]
        field_size = race["field_size"]
        tp_result = results.get((race["race_id"], tp["horse_id"]))
        tp_pos = tp_result[0] if tp_result else None
        tp_note = tp_result[1] if tp_result else None

        print(f"\n{race['off_time']}  {race['course_name']}  {race['race_name']}  ({field_size} runners)")
        tp_result_str = ("pos " + str(tp_pos)) if tp_pos else (tp_note if tp_note else "PENDING")
        print(f"  Top pick:  {tp['horse_name']:<24} model p={tp['model_probability']:.3f}  "
              f"price={'%.2f' % tp['exchange_back'] if tp['exchange_back'] else 'n/a'}  "
              f"result={tp_result_str}")

        if fav:
            fav_result = results.get((race["race_id"], fav["horse_id"]))
            fav_pos = fav_result[0] if fav_result else None
            fav_flag = "  <- also the top pick" if fav["horse_id"] == tp["horse_id"] else ""
            print(f"  Favourite: {fav['horse_name']:<24} price={fav['exchange_back']:.2f}  "
                  f"result={'pos ' + str(fav_pos) if fav_pos else 'PENDING'}{fav_flag}")
        else:
            print("  Favourite: no real market price available for this race")

        win_profit, win_note = settle_win(1.0, tp["exchange_back"], tp_pos, tp_note)
        ew_profit, ew_note = settle_each_way(2.0, tp["exchange_back"], tp_pos, field_size, tp_note)
        print(f"  £1 win stake:      {('£%.2f' % win_profit) if win_profit is not None else 'PENDING':<10} ({win_note})")
        print(f"  £2 each-way stake: {('£%.2f' % ew_profit) if ew_profit is not None else 'PENDING':<10} ({ew_note})")

        if win_profit is not None:
            win_total += win_profit
        else:
            win_pending += 1
        if ew_profit is not None:
            ew_total += ew_profit
        else:
            ew_pending += 1

    print(f"\n{'-' * 72}")
    print(f"  £1 WIN totals:      {'£%.2f' % win_total} settled"
          f"{f' ({win_pending} race(s) pending, not counted)' if win_pending else ''}")
    print(f"  £2 EACH-WAY totals: {'£%.2f' % ew_total} settled"
          f"{f' ({ew_pending} race(s) pending, not counted)' if ew_pending else ''}")
    print(f"{'=' * 72}\n")


if __name__ == "__main__":
    main()
