#!/usr/bin/env python3
"""Post-run integrity report + internal data-health page.

Recomputes classifications, settlement and the central metrics, asserts the
population identities, derives the Data Integrity Status from alerts, and
writes:
  logs/integrity_status.json   (consumed by the dashboards)
  data_health.html             (INTERNAL page; not under site/, never deployed)
Exit code 1 if any reconciliation identity fails.

Usage: python3 scripts/integrity_report.py [YYYY-MM-DD]
"""
import html
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg2

from scripts.integrity_migrate import SINCE, write_classifications
from src.integrity.health import collect_alerts, status_from_alerts
from src.integrity.metrics import compute, load_dataset, persist, reconcile

ROOT = Path(__file__).parent.parent


def today_panel(cur, today: date, now: datetime) -> dict:
    cur.execute("SELECT race_count, fetched_at FROM race_feed_snapshot WHERE target_date=%s ORDER BY fetched_at DESC LIMIT 1", (today,))
    feed = cur.fetchone()
    cur.execute("SELECT count(*) FILTER (WHERE status<>'RETIRED'), count(*) FROM canonical_race WHERE race_date=%s", (today,))
    active, ingested = cur.fetchone()
    cur.execute("""SELECT count(*) FILTER (WHERE status='VALID'), count(*) FILTER (WHERE status='QUARANTINED') FROM (
                     SELECT DISTINCT ON (v.race_id) v.status FROM race_validation v JOIN race r ON r.id=v.race_id
                     WHERE r.race_date=%s ORDER BY v.race_id, v.id DESC) x""", (today,))
    validated, quarantined = cur.fetchone()
    cur.execute("""SELECT count(DISTINCT pl.race_id) FROM prediction_lock pl JOIN race r ON r.id=pl.race_id
                   WHERE r.race_date=%s AND NOT EXISTS (SELECT 1 FROM excluded_race x WHERE x.race_id=r.id)""", (today,))
    locked = cur.fetchone()[0]
    cur.execute("""SELECT count(*), count(*) FILTER (WHERE has_lock) FROM (
                     SELECT r.id, EXISTS (SELECT 1 FROM price_observation po WHERE po.race_id=r.id AND po.back_price IS NOT NULL
                       AND po.price_quality='ok' AND po.captured_at BETWEEN
                         race_off_utc(r.race_date, r.off_time) - interval '30 minutes' AND
                         race_off_utc(r.race_date, r.off_time) - interval '60 seconds') has_lock
                     FROM race r WHERE r.race_date=%s AND race_off_utc(r.race_date, r.off_time) < %s
                       AND NOT EXISTS (SELECT 1 FROM excluded_race x WHERE x.race_id=r.id)) q""", (today, now))
    window_passed, with_lock = cur.fetchone()
    cur.execute("""SELECT count(*) FILTER (WHERE EXISTS (SELECT 1 FROM runner_result x WHERE x.race_id=r.id)),
                          count(*) FILTER (WHERE NOT EXISTS (SELECT 1 FROM runner_result x WHERE x.race_id=r.id))
                   FROM race r WHERE r.race_date=%s AND NOT EXISTS (SELECT 1 FROM excluded_race x WHERE x.race_id=r.id)""", (today,))
    settled, pending = cur.fetchone()
    return dict(expected_official_races=feed[0] if feed else None, feed_fetched_at=str(feed[1]) if feed else None,
                ingested_races=ingested, active_races=active, validated_races=validated, quarantined_races=quarantined,
                predictions_locked=locked, lock_window_passed=window_passed, with_lock_market=with_lock,
                market_coverage_pct=round(100 * with_lock / window_passed, 1) if window_passed else None,
                settled_races=settled, pending_races=pending)


def render_html(status, alerts, panel, c, checks, ds, generated):
    m = c["metrics"]
    def pct(x): return "n/a" if x is None else f"{x*100:.1f}%"
    rows = "".join(
        f"<tr><td>{html.escape(k)}</td><td>{'' if v.numerator is None else round(v.numerator, 2)}</td>"
        f"<td>{'' if v.denominator is None else round(v.denominator, 2)}</td><td>{pct(v.value)}</td>"
        f"<td>{v.sample_start or ''} → {v.sample_end or ''}</td><td class='d'>{html.escape(v.definition)}</td></tr>"
        for k, v in m.items())
    arows = "".join(f"<tr class='{a.severity}'><td>{a.severity}</td><td>{a.kind}</td><td>{html.escape(a.message)}</td><td>{html.escape(a.link)}</td></tr>"
                    for a in alerts) or "<tr><td colspan=4>No alerts.</td></tr>"
    crow = "".join(f"<tr class='{'OKR' if ok else 'CRITICAL'}'><td>{'PASS' if ok else 'FAIL'}</td><td>{html.escape(n)}</td><td>{a}</td><td>{b}</td></tr>" for n, a, b, ok in checks)
    prow = "".join(f"<tr><td>{k.replace('_',' ')}</td><td>{'—' if v is None else v}</td></tr>" for k, v in panel.items())
    exc = "".join(f"<tr><td>{r.facts.race_id}</td><td>{r.facts.race_date}</td><td>{r.facts.off_time}</td><td>{ds.classifications[r.facts.race_id].classification}</td><td class='d'>{html.escape(ds.classifications[r.facts.race_id].reason)}</td></tr>" for r in c["excluded"])
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Data Health</title><style>
:root{{--bg:#fff;--fg:#1c2230;--mut:#5b6577;--line:#d9dee7;--ok:#0f7b5f;--warn:#b26a00;--bad:#b3261e}}
@media (prefers-color-scheme:dark){{:root{{--bg:#12161d;--fg:#e6e9ef;--mut:#9aa3b2;--line:#2a3140;--ok:#46c29e;--warn:#e0a13a;--bad:#ff7b72}}}}
body{{background:var(--bg);color:var(--fg);font:14px/1.45 system-ui,sans-serif;margin:0;padding:16px;max-width:1100px;margin:auto}}
h1{{font-size:20px}}h2{{font-size:15px;margin-top:28px}}table{{border-collapse:collapse;width:100%;display:block;overflow-x:auto}}
td,th{{border-bottom:1px solid var(--line);padding:5px 8px;text-align:left;vertical-align:top}}.d{{color:var(--mut);font-size:12px}}
.s{{display:inline-block;padding:2px 10px;border-radius:12px;font-weight:600;color:#fff;background:{'var(--ok)' if status=='OK' else 'var(--warn)' if status=='WARNING' else 'var(--bad)'}}}
.CRITICAL td:first-child{{color:var(--bad);font-weight:600}}.WARN td:first-child{{color:var(--warn);font-weight:600}}.OKR td:first-child{{color:var(--ok);font-weight:600}}
</style></head><body><h1>Silent Edge Zero — Data Health <span class="s">{status}</span></h1>
<div class="d">Generated {generated:%Y-%m-%d %H:%M UTC} · dataset version {ds.version} · status is derived from the checks below, never set by hand · INTERNAL</div>
<h2>Today</h2><table>{prow}</table>
<h2>Alerts</h2><table><tr><th>Severity</th><th>Type</th><th>Detail</th><th>Raw record / audit log</th></tr>{arows}</table>
<h2>Population reconciliation</h2><table><tr><th></th><th>Identity</th><th>LHS</th><th>RHS</th></tr>{crow}</table>
<h2>Metrics (central layer)</h2><table><tr><th>Metric</th><th>Numerator</th><th>Denominator</th><th>Value</th><th>Sample</th><th>Definition</th></tr>{rows}</table>
<h2>Excluded races (preserved, not deleted)</h2><table><tr><th>Race</th><th>Date</th><th>Off</th><th>Class</th><th>Why</th></tr>{exc}</table>
</body></html>"""


def main():
    today = date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else date.today()
    now = datetime.now(timezone.utc)
    run_id = "report-" + now.strftime("%Y%m%dT%H%M%SZ")
    conn = psycopg2.connect(dbname="silent_edge_zero")
    cur = conn.cursor()
    ds = load_dataset(conn, SINCE, today)
    write_classifications(cur, ds, run_id)
    c = compute(ds)
    checks = reconcile(ds, c)
    persist(conn, ds, c, run_id)
    alerts = collect_alerts(conn, today, now, checks)
    status = status_from_alerts(alerts)
    panel = today_panel(cur, today, now)
    conn.commit()

    m = c["metrics"]
    cov_start, cov_end = m["settled_races"].sample_start, m["settled_races"].sample_end
    out = {"status": status, "generated_at": now.isoformat(), "dataset_version": ds.version, "today": panel,
           "alerts": [a.__dict__ for a in alerts], "reconciled": all(ok for *_, ok in checks),
           "metrics": {k: dict(numerator=v.numerator, denominator=v.denominator, value=v.value,
                               definition=v.definition, exclusions=v.exclusions,
                               sample_start=str(v.sample_start) if v.sample_start else None,
                               sample_end=str(v.sample_end) if v.sample_end else None) for k, v in m.items()}}
    (ROOT / "logs").mkdir(exist_ok=True)
    (ROOT / "logs" / "integrity_status.json").write_text(json.dumps(out, indent=2, default=str))
    (ROOT / "data_health.html").write_text(render_html(status, alerts, panel, c, checks, ds, now))

    print(f"DATA INTEGRITY STATUS: {status}  (dataset {ds.version}; settled sample {cov_start} → {cov_end})")
    for a in alerts:
        print(f"  [{a.severity}] {a.kind}: {a.message}")
    for n, a, b, ok in checks:
        print(f"  reconcile {'OK  ' if ok else 'FAIL'} {n}: {a} vs {b}")
    print("  today:", json.dumps(panel))
    conn.close()
    sys.exit(0 if all(ok for *_, ok in checks) else 1)


if __name__ == "__main__":
    main()
