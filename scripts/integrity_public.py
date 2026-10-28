"""Adapter: central metrics layer -> the shapes generate_dashboard.py already renders.

All public headline numbers flow from src/integrity/metrics.py, so the main
site, the research page and the data-health page can never disagree. Mixed
(non-homogeneous) P&L is always accompanied by its exchange-lock / other-
exchange / SP split.
"""
import html
from collections import defaultdict
from datetime import date

from scripts.generate_eod_report import ew_terms_for_field_size, settle_each_way
from src.integrity.market import choose_bet_price
from src.integrity.metrics import compute, settle_record
from src.integrity.settlement import PriceType, ResultStatus, classify_result, is_genuine_runner

EXCH = (PriceType.EXCHANGE_LOCK, PriceType.EXCHANGE_OTHER)


def _favourite(rec):
    """Market favourite = lowest pre-off EXCHANGE price (lock window preferred);
    SP favourite only if no runner has any exchange price (never mixed in a race)."""
    priced = []
    for x in rec.field:
        ch = choose_bet_price(x["quotes"], rec.off_dt, None)
        if ch.price_type in EXCH:
            priced.append((ch.price, x))
    if priced:
        return min(priced, key=lambda t: t[0])[1], "exchange"
    sps = [(x["sp"], x) for x in rec.field if x["sp"]]
    return (min(sps, key=lambda t: t[0])[1], "sp") if sps else (None, None)


def public_daily_summaries(ds, c=None) -> list:
    c = c or compute(ds)
    days = defaultdict(lambda: dict(races_total=0, races_settled=0, races_genuine=0, races_void=0, top_pick_wins=0, top_pick_placed=0,
                                    favourite_wins=0, win_stake_total=0.0, win_profit=0.0, ew_stake_total=0.0,
                                    ew_profit=0.0, sp_priced_races=0, n_lock=0, n_other=0, n_sp=0,
                                    pnl_lock=0.0, pnl_other=0.0, pnl_sp=0.0, pending=0))
    for r in c["valid"]:
        days[r.facts.race_date]["races_total"] += 1
    for r in c["pending"]:
        days[r.facts.race_date]["pending"] += 1
    for r in c["void"]:
        days[r.facts.race_date]["races_void"] += 1
        days[r.facts.race_date]["races_settled"] += 1      # settled = genuine runner + void (stake refunded)
    for r, st, ch in c["genuine"]:
        d = days[r.facts.race_date]
        d["races_settled"] += 1
        d["races_genuine"] += 1
        field_size = len(r.field)
        _, _, n_places = ew_terms_for_field_size(field_size)
        if st.status == ResultStatus.WIN:
            d["top_pick_wins"] += 1
        if r.top_position is not None and n_places and r.top_position <= n_places:
            d["top_pick_placed"] += 1
        fav, _ = _favourite(r)
        if fav is not None and fav["pos"] == 1:
            d["favourite_wins"] += 1
        if st.price is not None and st.settled:
            d["win_stake_total"] += 1.0
            d["win_profit"] += st.net_return
            ep, _ = settle_each_way(2.0, st.price, r.top_position, field_size, r.top_note)
            if ep is not None:
                d["ew_stake_total"] += 2.0
                d["ew_profit"] += ep
            key = {PriceType.EXCHANGE_LOCK: "lock", PriceType.EXCHANGE_OTHER: "other", PriceType.SP: "sp"}[st.price_type]
            d["n_" + key] += 1
            d["pnl_" + key] += st.net_return
            if key == "sp":
                d["sp_priced_races"] += 1
    out = []
    for race_date, d in sorted(days.items()):
        if d["races_settled"] <= 0:
            continue
        d = dict(d)          # keep full precision: rounding per day would break exact reconciliation
        d["race_date"] = race_date
        out.append(d)
    return out


def public_race_history(ds, c=None) -> dict:
    """{date: [row]} for the per-day popups. Statuses: WIN / PLACED / LOSS (incl. F/PU/UR...) /
    NR (true non-runner or void only) / PENDING."""
    c = c or compute(ds)
    out = defaultdict(list)
    for r in c["valid"]:
        field_size = len(r.field)
        _, _, n_places = ew_terms_for_field_size(field_size)
        status = classify_result(r.top_position, r.top_note, n_places)
        if status == ResultStatus.UNKNOWN_PENDING:
            ui = "PENDING"
        elif status == ResultStatus.WIN:
            ui = "WIN"
        elif status == ResultStatus.PLACED:
            ui = "PLACED"
        elif is_genuine_runner(status):
            ui = "LOSS"
        else:
            ui = "NR"
        out[r.facts.race_date].append({
            "off_time": r.facts.off_time, "course_name": r.facts.meeting.split("|")[1].title(),
            "race_name": r.facts.race_name, "horse_name": r.top_horse_name, "model_probability": r.top_prob,
            "finishing_position": r.top_position, "result_note": r.top_note, "field_size": field_size,
            "status": ui, "result_status": status.value})
    for k in out:
        out[k].sort(key=lambda x: x["off_time"])
    return dict(out)


def price_split(summaries: list) -> dict:
    t = defaultdict(float)
    for s in summaries:
        for k in ("n_lock", "n_other", "n_sp", "pnl_lock", "pnl_other", "pnl_sp"):
            t[k] += s.get(k, 0)
    return dict(t)


def _roi(p, n):
    return f"{p / n * 100:+.1f}%" if n else "n/a"


def render_integrity_panel(c: dict, status_info: dict, research_end: str | None) -> str:
    m = c["metrics"]
    ex = m["excluded_races"].exclusions
    cov = m["lock_market_coverage"]
    badge = {"OK": "good", "WARNING": "warn", "FAIL": "bad"}.get(status_info.get("status"), "warn")
    rows = []
    for key, label, tag in (("pnl_exchange_lock", "Exchange price at lock window", "executable"),
                            ("pnl_exchange_other", "Exchange price, earlier in the day", "exchange, not lock-time"),
                            ("pnl_sp", "Starting price (no exchange price existed)", "SP — not executable on the exchange"),
                            ("pnl_mixed", "ALL COMBINED — MIXED / NON-HOMOGENEOUS", "not equivalent to exchange ROI")):
        x = m[key]
        n = int(x.denominator or 0)
        rows.append(f"<tr><td>{html.escape(label)}<div class='ig-sub'>{html.escape(tag)}</div></td><td>{n}</td>"
                    f"<td>£{(x.numerator or 0):+.2f}</td><td>{_roi(x.numerator or 0, n)}</td></tr>")
    research = (f"<div class='ig-warn'>Research comparison currently valid through {html.escape(research_end)} only — "
                f"the paired model-vs-market sample has not advanced since.</div>") if research_end else ""
    return f"""
    <div class="section-label">Data integrity &amp; how these numbers are counted</div>
    <div class="ig-card">
      <div class="ig-head">Data Integrity Status: <span class="ig-badge ig-{badge}">{html.escape(status_info.get('status', 'UNKNOWN'))}</span>
        <span class="ig-sub">derived from automated checks · refreshed {html.escape(str(status_info.get('generated_at', ''))[:16].replace('T', ' '))} UTC</span></div>
      <div class="ig-pop">{int(m['raw_predicted_races'].numerator)} races predicted → {int(m['valid_races'].numerator)} valid
        ({int(m['excluded_races'].numerator)} excluded: {html.escape(', '.join(f'{v} {k.replace("_", " ").lower()}' for k, v in ex.items()) or 'none')})
        → {int(m['settled_races'].numerator)} settled + {int(m['pending_races'].numerator)} pending
        → {int(m['genuine_runner_races'].numerator)} genuine-runner top picks ({int(m['void_races'].numerator)} void/non-runner, stake refunded).</div>
      <div class="ig-pop">Top-pick win rate = {int(m['top_pick_win_rate'].numerator)} / {int(m['top_pick_win_rate'].denominator)} genuine runners
        ({m['top_pick_win_rate'].value * 100:.1f}%). Fell / pulled-up / unseated etc. count as losses, not non-runners.
        Sample {m['settled_races'].sample_start} → {m['settled_races'].sample_end}.</div>
      <table class="ig-table"><tr><th>£1 win on top pick — by price type</th><th>Bets</th><th>P&amp;L</th><th>ROI</th></tr>{''.join(rows)}</table>
      <div class="ig-pop">Lock-window exchange price coverage: {int(cov.numerator)} / {int(cov.denominator)} past races
        ({(cov.value or 0) * 100:.0f}%). Missing prices are never invented: such races settle at Starting Price (labelled) or are excluded.</div>
      <div class="ig-pop">This lifetime ROI covers every valid settled race since 2026-09-09. The Research Intelligence page's ROI covers
        only its own eligibility window and price type — different populations by design, not a contradiction.</div>
      {research}
    </div>
    <style>
      .ig-card{{border:1px solid var(--border,#d9dee7);border-radius:10px;padding:12px 14px;margin:8px 0 18px;font-size:13px;line-height:1.5}}
      .ig-head{{font-weight:600;margin-bottom:6px}}.ig-sub{{font-weight:400;opacity:.65;font-size:11px}}
      .ig-badge{{padding:2px 10px;border-radius:12px;color:#fff;font-weight:600}}.ig-good{{background:#0f7b5f}}.ig-warn{{background:#b26a00}}.ig-bad{{background:#b3261e}}
      .ig-pop{{margin:6px 0}}.ig-table{{border-collapse:collapse;width:100%;margin:8px 0;display:block;overflow-x:auto}}
      .ig-table td,.ig-table th{{padding:4px 8px;border-bottom:1px solid rgba(128,128,128,.25);text-align:left}}
      div.ig-warn{{background:rgba(178,106,0,.12);border-left:3px solid #b26a00;padding:6px 10px;margin-top:8px}}
    </style>"""
