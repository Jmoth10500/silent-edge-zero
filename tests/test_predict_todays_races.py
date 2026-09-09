"""
Real tests for scripts/predict_todays_races.py::record_hash — the pure
function behind the immutable prediction ledger's fingerprint (Section 32).
The rest of this script is DB-integration code (real INSERT/SELECT against
the live Postgres DB), exercised for real by running the script itself,
not by a synthetic-fixture unit test — same discipline as the other
one-shot scripts in this repo (train_model1.py, backfill_race_distance.py).
"""
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.predict_todays_races import record_hash


def test_record_hash_is_deterministic():
    ts = datetime(2026, 9, 9, 12, 0, 0, tzinfo=timezone.utc)
    h1 = record_hash(race_id=1, horse_id=2, model_version_id=3, model_probability=0.25, locked_at=ts)
    h2 = record_hash(race_id=1, horse_id=2, model_version_id=3, model_probability=0.25, locked_at=ts)
    assert h1 == h2


def test_record_hash_changes_with_any_field():
    ts = datetime(2026, 9, 9, 12, 0, 0, tzinfo=timezone.utc)
    base = record_hash(race_id=1, horse_id=2, model_version_id=3, model_probability=0.25, locked_at=ts)
    assert record_hash(race_id=99, horse_id=2, model_version_id=3, model_probability=0.25, locked_at=ts) != base
    assert record_hash(race_id=1, horse_id=99, model_version_id=3, model_probability=0.25, locked_at=ts) != base
    assert record_hash(race_id=1, horse_id=2, model_version_id=99, model_probability=0.25, locked_at=ts) != base
    assert record_hash(race_id=1, horse_id=2, model_version_id=3, model_probability=0.99, locked_at=ts) != base


def test_record_hash_is_a_real_sha256_hex_digest():
    ts = datetime(2026, 9, 9, 12, 0, 0, tzinfo=timezone.utc)
    h = record_hash(race_id=1, horse_id=2, model_version_id=3, model_probability=0.25, locked_at=ts)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


if __name__ == "__main__":
    tests = [
        test_record_hash_is_deterministic,
        test_record_hash_changes_with_any_field,
        test_record_hash_is_a_real_sha256_hex_digest,
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
