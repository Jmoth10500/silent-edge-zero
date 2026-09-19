#!/usr/bin/env python3
"""
Dashboard reconciliation — Silent Edge Zero V2 brief. Built directly in
response to Jonathan's own audit (2026-09-19) of the research dashboard,
which found four real cross-panel numeric inconsistencies and two
inaccurate narrative claims. Every check here asserts a SPECIFIC,
understood relationship between two numbers already shown on the page —
never "these should probably match", always "these must equal X because
of Y, and here's the exact race IDs behind any gap."

This is a hard gate: scripts/generate_research_dashboard.py calls
`run_reconciliation()` before writing the HTML file and refuses to
publish if any check fails (raises `ReconciliationError`). A failure here
means two panels on the same page would tell a reader two different,
unexplained numbers for what looks like the same thing — exactly the
defect this module exists to catch before anyone sees it.

**The four original discrepancies, root cause, and resolution:**

1. Four-way A+B (80) vs top-pick-outcome WON (81) — race 57666 (Chester,
   2026-09-12) won but had no usable market price at lock time, so it was
   UNRESOLVED in the four-way classification (excluded from A/B) while
   still counted as WON by the outcome breakdown (which never needed
   market data). FIXED: `top_pick_outcome_breakdown` now takes the same
   eligible race-id set the four-way classification uses, so A+B and WON
   are computed over the identical population and must match exactly —
   checked below.

2. "n=293 staked races" (297 in the reproduction) vs £271/£277 actually
   staked — the KPI card was labelling `races_settled` (every race with a
   known top-pick result, including 19 void/non-runner top picks and 1
   with no market price at all) as if it were the count of races that
   actually carried a real £1 stake. FIXED: `compute_roi` now returns
   both `n_settled` and `n_staked` separately, and the KPI card shows the
   real staked count with an explicit note about how many had no stake
   and why. Checked below: `n_staked` must equal `round(stake)` exactly
   (every real stake is a flat £1).

3. "124 model-market agreements" vs "119" in the SE-rank-1/market-rank-1
   heat-map cell — a genuine SEMANTIC difference, not a bug: agreement is
   a pre-race property (which horse each side picked, before anything
   happens), so a void/non-runner top pick can still count as "agreed"
   even though it never produced a real win/loss outcome for the heat
   map to score. The exact races behind the gap are non-runner top picks
   in an otherwise-agreeing pair. NOT collapsed to one number — both stay
   on the page, but the gap is now checked and must equal exactly the
   count of agreeing races whose top pick was void/non-runner.

4. Heat-map runner-population sum (2,229) vs Brier paired-observation
   count (2,225) — a real bug: `rank_by_market` trivially assigns a rank
   even to the SOLE priced runner in a field (nothing to rank against),
   but a market PROBABILITY needs >=2 real priced runners to de-vig at
   all. `ranking_matrix.build_rank_observations` used to keep such a
   runner in the population (with `market_probability=None`) while
   `brier_live.compute_paired_observations` correctly excluded the whole
   race. FIXED: `build_rank_observations` now requires the race to be
   de-vig-able at all, matching brier_live's population exactly. Checked
   below: the two totals must now be identical.

**The two narrative corrections** (Jonathan's own wording):
- "Both wrong" (category D) does NOT mean "they agreed" — they can pick
  two different losing horses. Fixed in build_insights' four-way text,
  which now reports the real split of D into genuine-agreement-that-lost
  vs genuine-disagreement-that-both-lost (`split_both_wrong_by_agreement`).
- "Disagreement" does NOT establish statistical independence — picking
  different horses says nothing about whether the two forecasting
  processes are independent in any formal sense. Fixed in the KPI
  summary text.

**Second audit round (2026-09-20), three further findings — all real,
none were the original four bugs recurring:**

5. Missed-winner 0-10% band (95) vs ALL-RUNNERS 0-10% band actual_wins
   (86) — NOT a bug, a genuine undisclosed population difference: 23 of
   those 95 missed winners have no market price of their own even though
   their race overall was de-vig-able. FIXED: `missed_winner_probability_
   bands` now reports `n_winners_priced`/`n_winners_unpriced` per band (a
   true subset of the ALL-RUNNERS population), and Check 8 below enforces
   `n_winners_priced <= ALL-RUNNERS actual_wins` band by band.

6. "127 agreements" vs four-way A+D-agree (126) — NOT a bug, a genuine
   joint-favourite edge case (race 57991, Kelso, 2026-09-16): see
   `count_joint_favourite_agree_but_market_only_correct`'s docstring.
   FIXED: Check 6 below enforces agree == A + D-agree + joint-favourite-C
   with no remainder.

7. "295 outcomes" vs "327 settled races" — NOT a bug, the same class of
   eligible-vs-settled population gap as the original discrepancy #3,
   now given a full exact accounting via `compute_settled_race_ids` and
   Check 7 below (two sub-checks: roi.n_settled against the independently
   computed settled set, and the outcome-breakdown total against the
   eligible/settled intersection).
"""
from datetime import date, timedelta

from scripts.generate_eod_report import VOID_RESULT_CODES, load_results, load_top_picks_and_favourites


def compute_settled_race_ids(conn, start: date, end: date) -> set[int]:
    """Real, exact set of race_ids that daily_summary's own
    `races_settled` counts — every race where the TOP PICK's own result
    is known (win, loss, or terminal void/non-runner note), regardless of
    whether market data exists. Computed directly from the same
    load_top_picks_and_favourites/load_results functions
    generate_daily_summary.py itself uses, so `len(this set)` reconciles
    exactly with `SUM(races_settled)` from the real daily_summary table —
    used to name the exact race-level accounting between "eligible"
    (needs market data) and "settled" (doesn't), rather than leaving that
    gap as an unverified label."""
    settled: set[int] = set()
    d = start
    while d <= end:
        races = load_top_picks_and_favourites(conn, d)
        results = load_results(conn, d)
        for race in races:
            tp = race["top_pick"]
            tp_result = results.get((race["race_id"], tp["horse_id"]))
            tp_pos = tp_result[0] if tp_result else None
            tp_note = tp_result[1] if tp_result else None
            if tp_pos is None and tp_note is None:
                continue
            settled.add(race["race_id"])
        d += timedelta(days=1)
    return settled


class ReconciliationError(Exception):
    """Raised when the dashboard's own numbers don't reconcile. Blocks
    publication — main() must not write the HTML file if this is raised."""


def count_void_agree_races_from_races(races: list[dict], classified: list[dict]) -> dict:
    """Real count of races where Silent Edge and the market agreed on the
    top pick (pre-race) but that horse was a void/non-runner — the exact
    accounting for discrepancy #3 above. Needs the raw `races` list (not
    just `classified`) since agreement/classification data alone doesn't
    carry the top pick's own result note."""
    by_race_id = {c["race_id"]: c for c in classified}
    void_agree_ids = []
    for race in races:
        c = by_race_id.get(race["race"]["race_id"])
        if c is None or c["category"] == "UNRESOLVED":
            continue
        top_pick_id = c["top_pick_horse_id"]
        if top_pick_id not in c["favourite_horse_ids"]:
            continue  # not agreement
        top_pick_runner = next((r for r in race["runners"] if r["horse"]["horse_id"] == top_pick_id), None)
        if top_pick_runner is None:
            continue
        note = top_pick_runner["result"]["result_note"]
        if note in VOID_RESULT_CODES:
            void_agree_ids.append(race["race"]["race_id"])
    return {"n": len(void_agree_ids), "race_ids": void_agree_ids}


def count_joint_favourite_agree_but_market_only_correct(classified: list[dict]) -> dict:
    """Real, previously-undisclosed edge case found in Jonathan's second
    audit (2026-09-20): "agree" (top_pick is ONE of the market's real
    favourites) does not only decompose into category A (same horse won)
    and category D-agree (same horse lost). With a genuine JOINT
    favourite, Silent Edge's top pick can be one tied favourite while a
    DIFFERENT tied favourite actually wins — the market is still correct
    (the winner IS among its favourites) but Silent Edge's specific pick
    lost, which is category C, not A or D. Exact case found live: race
    57991 (Kelso, 2026-09-16) — favourites [82750, 82749], top pick
    82750, winner 82749. Category B is structurally impossible for an
    agreeing race (if top_pick==winner and top_pick is a favourite, the
    winner is trivially also a favourite, making it category A by
    definition) — this function's result plus A and D-agree must account
    for every real "agree" race with no remainder."""
    ids = [
        c["race_id"] for c in classified
        if c["category"] == "C" and c["top_pick_horse_id"] in c["favourite_horse_ids"]
    ]
    return {"n": len(ids), "race_ids": ids}


def run_reconciliation(all_races: list[dict], classified: list[dict], class_summary: dict,
                        outcome_breakdown: dict, roi: dict, agreement_splits: dict,
                        rank_matrix: dict, brier_summary: dict | None, d_split: dict,
                        eligible_race_ids: set[int], settled_race_ids: set[int],
                        missed_bands: dict, all_runners_bands: dict) -> dict:
    """Runs every reconciliation check. Returns a detail dict regardless
    of outcome; raises ReconciliationError (never returns a "FAIL" status
    silently) if any check does not hold, so a caller cannot accidentally
    ignore a failure."""
    checks = []

    # Check 1: four-way A+B must equal outcome-breakdown WON exactly,
    # now that both are computed over the identical eligible population.
    fw = class_summary["four_way"]
    ab = fw["A"] + fw["B"]
    won = outcome_breakdown["WON"]
    checks.append({
        "name": "four_way_AB_equals_outcome_WON",
        "passed": ab == won,
        "detail": f"four-way A+B={ab}, outcome-breakdown WON={won}",
    })

    # Check 2: n_staked must equal round(stake) exactly (flat £1 stakes).
    checks.append({
        "name": "roi_n_staked_equals_rounded_stake",
        "passed": roi["n_staked"] == round(roi["stake"]),
        "detail": f"n_staked={roi['n_staked']}, round(stake)={round(roi['stake'])}",
    })
    checks.append({
        "name": "roi_n_staked_le_n_settled",
        "passed": roi["n_staked"] <= roi["n_settled"],
        "detail": f"n_staked={roi['n_staked']}, n_settled={roi['n_settled']}",
    })

    # Check 3: SE-vs-market "agree" count must equal the heat-map's
    # rank1/rank1 cell population PLUS the exact count of agreeing races
    # whose top pick was a void/non-runner (a real, named, counted gap —
    # never an unexplained one).
    void_agree = count_void_agree_races_from_races(all_races, classified)
    cell_11 = rank_matrix.get("se_rank=1,market_rank=1")
    cell_11_n = cell_11["n"] if cell_11 else 0
    agree_n = agreement_splits["silent_edge_vs_market"]["agree"]["n"]
    checks.append({
        "name": "agreement_reconciles_with_heatmap_cell_via_void_top_picks",
        "passed": agree_n == cell_11_n + void_agree["n"],
        "detail": (f"agree={agree_n}, heat-map cell(1,1)={cell_11_n}, "
                   f"void-top-pick-agree={void_agree['n']} (race ids {void_agree['race_ids']})"),
    })

    # Check 4: heat-map total runner population must equal the Brier
    # paired-observation count exactly (both now require the same
    # de-vig-able-race population, by construction after the fix).
    heatmap_total_n = sum(c["n"] for c in rank_matrix.values())
    brier_n = brier_summary["n"] if brier_summary else 0
    checks.append({
        "name": "heatmap_population_equals_brier_population",
        "passed": heatmap_total_n == brier_n,
        "detail": f"heat-map total n={heatmap_total_n}, Brier n={brier_n}",
    })

    # Check 5: the D-split (both-wrong-agree + both-wrong-disagree) must
    # sum back to the four-way D count exactly — a sanity check on the
    # new split itself, not just the numbers it's built from.
    checks.append({
        "name": "d_split_sums_to_four_way_D",
        "passed": d_split["agree"] + d_split["disagree"] == fw["D"],
        "detail": f"d_split agree+disagree={d_split['agree']+d_split['disagree']}, four-way D={fw['D']}",
    })

    # Check 6: real 2026-09-20 finding — "agree" (top_pick is a real market
    # favourite) does not only decompose into A (same horse won) and
    # D-agree (same horse lost). A genuine JOINT favourite lets Silent
    # Edge's top pick be one tied favourite while a DIFFERENT tied
    # favourite wins -- market correct, Silent Edge wrong -- category C,
    # not A or D. Category B is structurally impossible for an agreeing
    # race (see count_joint_favourite_agree_but_market_only_correct's own
    # docstring), so A + D-agree + this-C-case must equal agree_n exactly
    # with no remainder.
    joint_fav_c = count_joint_favourite_agree_but_market_only_correct(classified)
    checks.append({
        "name": "agreement_decomposes_exactly_into_A_plus_D_agree_plus_joint_favourite_C",
        "passed": agree_n == fw["A"] + d_split["agree"] + joint_fav_c["n"],
        "detail": (f"agree={agree_n}, four-way A={fw['A']}, D-agree={d_split['agree']}, "
                   f"joint-favourite-C={joint_fav_c['n']} (race ids {joint_fav_c['race_ids']})"),
    })

    # Check 7: the real, exact accounting behind "eligible races" (needs
    # market data) vs "settled races" (daily_summary's own count, doesn't
    # need market data) — two genuinely different populations that must
    # never be silently left as an unreconciled pair of headline numbers
    # (Jonathan's 2026-09-20 finding: 295 vs 327). roi.n_settled must
    # equal the independently-computed settled-race-id set exactly (an
    # integrity check on daily_summary itself), and the outcome-breakdown
    # total must equal exactly the INTERSECTION of eligible and settled —
    # races that are both.
    outcome_total = sum(outcome_breakdown.values())
    intersection_n = len(eligible_race_ids & settled_race_ids)
    checks.append({
        "name": "roi_n_settled_equals_independently_computed_settled_set",
        "passed": roi["n_settled"] == len(settled_race_ids),
        "detail": f"roi.n_settled={roi['n_settled']}, independently computed settled set size={len(settled_race_ids)}",
    })
    checks.append({
        "name": "outcome_breakdown_total_equals_eligible_and_settled_intersection",
        "passed": outcome_total == intersection_n,
        "detail": (f"outcome_breakdown total={outcome_total}, |eligible ∩ settled|={intersection_n} "
                   f"(eligible-only: {sorted(eligible_race_ids - settled_race_ids)}, "
                   f"settled-only: {sorted(settled_race_ids - eligible_race_ids)[:10]}"
                   f"{'...' if len(settled_race_ids - eligible_race_ids) > 10 else ''})"),
    })

    # Check 8: real 2026-09-20 finding — a missed winner can lack its own
    # market price even when its race was overall de-vig-able, so
    # n_winners (missed-winner chart) is NOT a valid subset of the
    # ALL-RUNNERS Brier/calibration population for the same band. The
    # PRICED subset (n_winners_priced) IS a true subset, since it applies
    # the identical per-runner pricing rule — this must never exceed the
    # corresponding ALL-RUNNERS actual-win count, band by band.
    for band_key, missed_band in missed_bands.items():
        all_runners_band = all_runners_bands.get(band_key)
        actual_wins = all_runners_band["actual_wins"] if all_runners_band else 0
        checks.append({
            "name": f"missed_winner_priced_subset_le_all_runners_actual_wins[{band_key}]",
            "passed": missed_band["n_winners_priced"] <= actual_wins,
            "detail": (f"band {band_key}: missed-winner priced n={missed_band['n_winners_priced']} "
                       f"(of {missed_band['n_winners']} total, {missed_band['n_winners_unpriced']} unpriced), "
                       f"ALL-RUNNERS actual_wins={actual_wins}"),
        })

    failures = [c for c in checks if not c["passed"]]
    result = {"status": "FAIL" if failures else "PASS", "checks": checks}

    if failures:
        lines = "\n".join(f"  - {c['name']}: {c['detail']}" for c in failures)
        raise ReconciliationError(
            f"Dashboard reconciliation FAILED — refusing to publish. {len(failures)} check(s) failed:\n{lines}"
        )

    return result
