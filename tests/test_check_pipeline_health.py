"""
Real tests for scripts/check_pipeline_health.py's file-based check
(check_deploy_log_fresh) — the only check here with no DB dependency.
The DB-backed checks are exercised by actually running the script
against the real database, same convention as every other operational
script in this repo.
"""
import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import scripts.check_pipeline_health as health


def test_check_deploy_log_fresh_missing_file():
    with tempfile.TemporaryDirectory() as d:
        health.LOG_DIR = Path(d)
        ok, detail = health.check_deploy_log_fresh(date(2026, 9, 11))
        assert ok is False
        assert "does not exist" in detail


def test_check_deploy_log_fresh_stale_mtime():
    with tempfile.TemporaryDirectory() as d:
        health.LOG_DIR = Path(d)
        log = Path(d) / "predict_races.log"
        log.write_text("Deploy is live!")
        yesterday_ts = (date.today() - timedelta(days=1)).toordinal() * 86400
        os.utime(log, (yesterday_ts, yesterday_ts))
        ok, detail = health.check_deploy_log_fresh(date.today())
        assert ok is False
        assert "not today" in detail


def test_check_deploy_log_fresh_missing_deploy_line():
    with tempfile.TemporaryDirectory() as d:
        health.LOG_DIR = Path(d)
        log = Path(d) / "predict_races.log"
        log.write_text("some output but no real deploy confirmation")
        ok, detail = health.check_deploy_log_fresh(date.today())
        assert ok is False
        assert "Deploy is live" in detail


def test_check_deploy_log_fresh_success_case():
    with tempfile.TemporaryDirectory() as d:
        health.LOG_DIR = Path(d)
        log = Path(d) / "predict_races.log"
        log.write_text("...\nDeploy is live!\n")
        (Path(d) / "predict_races_error.log").write_text("")
        ok, detail = health.check_deploy_log_fresh(date.today())
        assert ok is True
        assert "fresh" in detail


def test_check_deploy_log_fresh_harmless_stderr_not_flagged():
    """Real, observed shape (2026-09-10 07:36 run): a harmless
    'env: node: No such file' line at the top of stderr, followed by the
    real netlify CLI sequence ending in its own 'Deploy is live!' line —
    should NOT be treated as a real error."""
    with tempfile.TemporaryDirectory() as d:
        health.LOG_DIR = Path(d)
        (Path(d) / "predict_races.log").write_text("...\nDeploy is live!\n")
        (Path(d) / "predict_races_error.log").write_text(
            "env: node: No such file or directory\n...\n✔ Deploy is live!\n"
        )
        ok, detail = health.check_deploy_log_fresh(date.today())
        assert ok is True
        assert "stderr has content" not in detail


def test_check_deploy_log_fresh_success_marker_only_in_stderr():
    """Real, observed shape (2026-09-12 09:03 run): stdout carried its
    own real 'Deploy complete' line but NOT the literal 'Deploy is
    live!' text (which landed in stderr instead, twice) — Netlify's own
    stdout/stderr allocation for these lines isn't consistent run to
    run. Confirmed live the deploy genuinely succeeded (the site's own
    title tag showed the real current date) despite stdout alone not
    containing 'Deploy is live!' — must not be a false-positive FAIL."""
    with tempfile.TemporaryDirectory() as d:
        health.LOG_DIR = Path(d)
        (Path(d) / "predict_races.log").write_text("...\nDeploy complete\n...\n")
        (Path(d) / "predict_races_error.log").write_text(
            "env: node: No such file or directory\n...\nDeploy is live!\n...\nDeploy is live!\n"
        )
        ok, detail = health.check_deploy_log_fresh(date.today())
        assert ok is True
        assert "fresh" in detail


def test_check_deploy_log_fresh_real_failure_no_marker_anywhere():
    with tempfile.TemporaryDirectory() as d:
        health.LOG_DIR = Path(d)
        (Path(d) / "predict_races.log").write_text("some output, no success line\n")
        (Path(d) / "predict_races_error.log").write_text("env: node: No such file or directory\n")
        ok, detail = health.check_deploy_log_fresh(date.today())
        assert ok is False
        assert "may have failed" in detail


if __name__ == "__main__":
    tests = [
        test_check_deploy_log_fresh_missing_file,
        test_check_deploy_log_fresh_stale_mtime,
        test_check_deploy_log_fresh_missing_deploy_line,
        test_check_deploy_log_fresh_success_case,
        test_check_deploy_log_fresh_harmless_stderr_not_flagged,
        test_check_deploy_log_fresh_success_marker_only_in_stderr,
        test_check_deploy_log_fresh_real_failure_no_marker_anywhere,
    ]
    passed = 0
    for t in tests:
        print(f"{t.__name__}:")
        try:
            t()
            print("  PASS")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL: {e}")
    print(f"\n{passed}/{len(tests)} tests passed.")
    sys.exit(0 if passed == len(tests) else 1)
