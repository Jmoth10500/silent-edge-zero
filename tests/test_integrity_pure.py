"""Integrity layer, pure-logic tests (no DB): canonical identity, validation gate,
settlement taxonomy, market price rules. Covers spec tests 1-4, 6-10, 13."""
from datetime import date, datetime, timedelta, timezone

import pytest

from src.integrity.canonical import (
    base_race_label, build_input_snapshot, canonical_race_id, horse_key, meeting_id, parse_division,
)
from src.integrity import market
from src.integrity.classify import RaceFacts, classify_races
from src.integrity.market import Quote, choose_bet_price, fallback_decision, lock_market_state
from src.integrity.settlement import (
    PriceType, ResultStatus, classify_result, is_genuine_runner, settle_win_bet,
)
from src.integrity.validation import (
    RaceView, V01_CANONICAL_ID, V02_NOT_IN_LATEST_FEED, V05_DUPLICATE_PROVIDER_ID, V06_DUPLICATE_RUNNER,
    V07_RUNNER_IN_MULTIPLE_RACES, V08_RUNNER_COUNT, V09_ABANDONED, V10_SNAPSHOT_TIMESTAMP,
    V11_STALE_OVERWRITE, V12_DUPLICATE_RACE_LABEL, validate_races,
)

D = date(2026, 10, 16)
NOW = datetime(2026, 10, 16, 7, 30, tzinfo=timezone.utc)
UTC = timezone.utc


def view(race_id, pid, off, name, runners, course="Redcar", **kw):
    base = dict(race_id=race_id, canonical_race_id=f"P:{pid}", provider_race_id=pid, race_date=D, snapshot_date=D,
                meeting_id=meeting_id(D, course), course_name=course, off_time=off, race_name=name,
                runner_names=runners, feed_runner_count=len(runners), snapshot_at=NOW - timedelta(minutes=5))
    base.update(kw)
    return RaceView(**base)


def horses(prefix, n):
    return [f"{prefix} {i} (GB)" for i in range(n)]


# ---------------------------------------------------------------- TEST 1
def test_reschedule_does_not_change_canonical_identity():
    a, _ = canonical_race_id("rac_1", D, "Redcar")
    b, _ = canonical_race_id("rac_1", D, "Redcar")      # same provider id, any off-time
    assert a == b == "P:rac_1"


def test_composite_identity_never_uses_off_time():
    cid, basis = canonical_race_id(None, D, "Redcar", sequence=3, division="II")
    assert basis == "COMPOSITE" and "13:55" not in cid and cid.endswith("|3|II")
    with pytest.raises(ValueError):
        canonical_race_id(None, D, "Redcar")


# ---------------------------------------------------------------- TEST 2
def test_division_one_and_two_cannot_be_merged_or_duplicated():
    assert parse_division("Novice Stakes (Div I) (GBB Race)") == "I"
    assert parse_division("Novice Stakes (Div II)") == "II"
    assert base_race_label("Novice Stakes (Div I)") == base_race_label("Novice Stakes (Div II)")
    div1 = view(1, "a", "13:20:00", "Novice Stakes (Div I)", horses("A", 10))
    div2 = view(2, "b", "13:52:00", "Novice Stakes (Div II)", horses("B", 10))
    assert all(r.ok for r in validate_races([div1, div2], NOW))      # legitimate pair passes
    dup = view(3, "c", "13:55:00", "Novice Stakes (Div I)", horses("A", 10) + horses("C", 18))
    res = {r.race_id: r for r in validate_races([div1, div2, dup], NOW)}
    assert V12_DUPLICATE_RACE_LABEL in res[3].failed_rules and not res[3].ok
    assert not res[1].ok                       # the real Div I is also held for review (cannot tell which is real)


# ---------------------------------------------------------------- TEST 3
def test_one_provider_race_id_cannot_create_multiple_scored_predictions():
    a = view(1, "same", "14:00:00", "Race A", horses("A", 8))
    b = view(2, "same", "14:05:00", "Race A rescheduled", horses("A", 8))
    b.canonical_race_id = "P:same"
    res = validate_races([a, b], NOW)
    assert all(not r.ok for r in res)
    assert all(V05_DUPLICATE_PROVIDER_ID in r.failed_rules and V01_CANONICAL_ID in r.failed_rules for r in res)


# ---------------------------------------------------------------- TEST 4
def test_horse_in_two_simultaneous_races_triggers_quarantine():
    shared = "My Girl Dee Mo (IRE)"
    r1 = view(1, "a", "13:52:00", "Handicap One", horses("A", 9) + [shared])
    r2 = view(2, "b", "13:55:00", "Handicap Two", horses("B", 9) + [shared.replace("(IRE)", "(GB)")])
    res = {r.race_id: r for r in validate_races([r1, r2], NOW)}
    assert V07_RUNNER_IN_MULTIPLE_RACES in res[1].failed_rules and V07_RUNNER_IN_MULTIPLE_RACES in res[2].failed_rules


def test_duplicate_runner_inside_one_race():
    r = view(1, "a", "13:00:00", "X", ["Same Horse (GB)", "same horse", "Other (IRE)"])
    assert V06_DUPLICATE_RUNNER in validate_races([r], NOW)[0].failed_rules


# ---------------------------------------------------------------- TEST 6
def test_stale_feed_cannot_overwrite_newer_snapshot():
    r = view(1, "a", "13:00:00", "X", horses("A", 6), superseding_snapshot_at=NOW)
    assert V11_STALE_OVERWRITE in validate_races([r], NOW)[0].failed_rules


def test_snapshot_timestamp_and_feed_membership_and_abandonment():
    assert V10_SNAPSHOT_TIMESTAMP in validate_races([view(1, "a", "13:00:00", "X", horses("A", 6), snapshot_at=None)], NOW)[0].failed_rules
    assert V10_SNAPSHOT_TIMESTAMP in validate_races([view(1, "a", "13:00:00", "X", horses("A", 6), snapshot_at=NOW + timedelta(hours=2))], NOW)[0].failed_rules
    assert V02_NOT_IN_LATEST_FEED in validate_races([view(1, "a", "13:00:00", "X", horses("A", 6), in_latest_feed=False)], NOW)[0].failed_rules
    assert V09_ABANDONED in validate_races([view(1, "a", "13:00:00", "X", horses("A", 6), status="ABANDONED")], NOW)[0].failed_rules
    assert V08_RUNNER_COUNT in validate_races([view(1, "a", "13:00:00", "X", horses("A", 1))], NOW)[0].failed_rules
    assert V08_RUNNER_COUNT in validate_races([view(1, "a", "13:00:00", "X", horses("A", 190))], NOW)[0].failed_rules
    assert V08_RUNNER_COUNT in validate_races([view(1, "a", "13:00:00", "X", horses("A", 6), feed_runner_count=9)], NOW)[0].failed_rules


# ---------------------------------------------------------------- TEST 13
def test_16_oct_redcar_haydock_anomalies_cannot_be_reproduced():
    """The exact 16 Oct shapes: provisional entries cards alongside the real declared cards."""
    my_girl = "My Girl Dee Mo (GB)"
    div1 = view(59877, "rac_32301643868", "13:20:00", "Join Racing TV Now British EBF Restricted Novice Stakes (Div I) (GBB Race)", horses("R1", 9) + ["Kitty (GB)"])
    div2 = view(59878, "rac_32301645805", "13:52:00", "Join Racing TV Now British EBF Restricted Novice Stakes (Div II) (GBB Race)", horses("R2", 9) + [my_girl])
    phantom = view(59879, "rac_32301240972", "13:55:00", "Join Racing TV Now British EBF Restricted Novice Stakes (Div I) (GBB Race)",
                   horses("R1", 9) + ["Kitty (GB)"] + horses("R2", 9) + [my_girl] + horses("RX", 8))
    res = {r.race_id: r for r in validate_races([div1, div2, phantom], NOW)}
    assert not res[59879].ok and not res[59879].failed_rules == []
    assert V12_DUPLICATE_RACE_LABEL in res[59879].failed_rules and V07_RUNNER_IN_MULTIPLE_RACES in res[59879].failed_rules

    hay = "Venetian Lion (GB)"
    h1 = view(59860, "h1", "14:17:00", "M6Toll Road To Victory Handicap Stakes (Div I)", horses("H1", 9) + ["Foo (GB)"], course="Haydock")
    h2 = view(59861, "h2", "14:52:00", "M6Toll Road To Victory Handicap Stakes (Div II)", horses("H2", 9) + [hay], course="Haydock")
    hp = view(59859, "h0", "14:12:00", "M6Toll Road To Victory Handicap Stakes (Div I)", horses("H1", 9) + ["Foo (GB)"] + horses("H2", 9) + [hay] + horses("HX", 11), course="Haydock")
    s1 = view(59866, "s1", "17:07:00", "Shape Engineering Handicap Stakes", horses("S", 14), course="Haydock")
    s0 = view(59864, "s0", "16:32:00", "Shape Engineering Handicap Stakes", horses("S", 14) + horses("SX", 12), course="Haydock")
    hres = {r.race_id: r for r in validate_races([h1, h2, hp, s1, s0], NOW)}
    assert not hres[59859].ok and not hres[59864].ok
    # and the history classifier excludes them as superseded duplicates
    facts = [RaceFacts(i, D, meeting_id(D, "Haydock"), "", f"p{i}", "n", frozenset(horse_key(n) for n in names), [(1, None)] if i == 59866 else [(None, None)])
             for i, names in ((59859, hp.runner_names), (59860, h1.runner_names), (59861, h2.runner_names))]
    cls = classify_races(facts, date(2026, 10, 17))
    assert cls[59859].classification == "INVALID_DUPLICATE" and not cls[59859].include_in_metrics


# ---------------------------------------------------------------- TEST 5 (pure half)
def test_input_snapshot_hash_detects_runner_list_mutation():
    kw = dict(canonical_race_id="P:x", meeting="m", source_race_id="x", source_snapshot_at="t", scheduled_off_time="13:00:00",
              model_version="gbm_v1:1.1", probabilities={1: 0.6, 2: 0.4}, locked_at="L")
    a = build_input_snapshot(runners=[(1, "A"), (2, "B")], **kw).sha256()
    assert a == build_input_snapshot(runners=[(2, "B"), (1, "A")], **kw).sha256()        # order-independent
    assert a != build_input_snapshot(runners=[(1, "A"), (2, "B"), (3, "C")], **{**kw, "probabilities": {1: 0.6, 2: 0.4, 3: 0.0}}).sha256()
    assert a != build_input_snapshot(runners=[(1, "A"), (2, "B")], **{**kw, "probabilities": {1: 0.61, 2: 0.39}}).sha256()


# ---------------------------------------------------------------- TEST 10
@pytest.mark.parametrize("note,expected", [
    ("PU", ResultStatus.PULLED_UP), ("F", ResultStatus.FELL), ("FELL", ResultStatus.FELL), ("UR", ResultStatus.UNSEATED),
    ("SU", ResultStatus.UNSEATED), ("U", ResultStatus.UNSEATED), ("BD", ResultStatus.BROUGHT_DOWN), ("RR", ResultStatus.REFUSED),
    ("REF", ResultStatus.REFUSED), ("RO", ResultStatus.RAN_OUT), ("CO", ResultStatus.CARRIED_OUT), ("DSQ", ResultStatus.DISQUALIFIED),
])
def test_failures_to_finish_are_losses_not_non_runners(note, expected):
    status = classify_result(None, note)
    assert status == expected and is_genuine_runner(status)
    s = settle_win_bet(1.0, 5.0, PriceType.EXCHANGE_LOCK, status)
    assert s.settled and s.net_return == -1.0 and s.gross_return == 0.0


@pytest.mark.parametrize("note,expected", [("NR", ResultStatus.NON_RUNNER), ("VOID", ResultStatus.VOID), ("WD", ResultStatus.NON_RUNNER)])
def test_only_true_non_runners_and_void_refund(note, expected):
    status = classify_result(None, note)
    assert status == expected and not is_genuine_runner(status)
    s = settle_win_bet(1.0, 5.0, PriceType.SP, status)
    assert s.net_return == 0.0 and s.gross_return == 1.0


def test_win_place_unplaced_pending_and_unknown():
    assert classify_result(1, None) == ResultStatus.WIN
    assert classify_result(3, None, n_places=3) == ResultStatus.PLACED
    assert classify_result(4, None, n_places=3) == ResultStatus.FINISHED_UNPLACED
    assert classify_result(None, None) == ResultStatus.UNKNOWN_PENDING
    assert classify_result(None, "ZZZ") == ResultStatus.UNKNOWN_PENDING          # never guessed
    assert settle_win_bet(1.0, 5.0, PriceType.SP, ResultStatus.UNKNOWN_PENDING).settled is False
    w = settle_win_bet(1.0, 5.0, PriceType.EXCHANGE_LOCK, ResultStatus.WIN, commission_rate=0.02)
    assert w.net_return == pytest.approx(4.0 - 0.08) and w.commission == pytest.approx(0.08)
    assert settle_win_bet(1.0, 5.0, PriceType.SP, ResultStatus.WIN, commission_rate=0.02).commission == 0.0
    assert settle_win_bet(1.0, None, PriceType.NO_PRICE, ResultStatus.WIN).settled is False


# ---------------------------------------------------------------- TEST 7 / 8
OFF = datetime(2026, 10, 16, 13, 0, tzinfo=UTC)


def q(minutes_before_off, back=5.0, **kw):
    return Quote(back, kw.pop("lay", 5.2), OFF - timedelta(minutes=minutes_before_off), **kw)


def test_missing_market_data_is_null_never_invented():
    c = choose_bet_price([], OFF, sp=None)
    assert c.price is None and c.price_type == PriceType.NO_PRICE and c.reason == market.NULL_PRIMARY_DOWN
    assert lock_market_state([], OFF) == "NONE"


def test_post_race_price_never_used_as_lock_time_observation():
    post = [q(-5), q(-30, back=2.0)]                                 # captured 5 and 30 min AFTER the off
    c = choose_bet_price(post, OFF, sp=None)
    assert c.price_type == PriceType.NO_PRICE and c.reason == market.NULL_AFTER_OFF
    assert lock_market_state(post, OFF) == "NONE"
    # a price 30s before the off is inside the 60s buffer: also not usable
    assert choose_bet_price([q(0.5)], OFF, sp=None).price_type == PriceType.NO_PRICE
    # post-off price + SP available => SP, still never the post-off exchange price
    c = choose_bet_price(post, OFF, sp=4.0)
    assert c.price_type == PriceType.SP and c.price == 4.0


def test_lock_window_other_and_quality_rules():
    assert choose_bet_price([q(10, 6.0), q(2, 4.0)], OFF, None).price == 4.0                 # last valid in window
    assert choose_bet_price([q(10, 6.0), q(2, 4.0)], OFF, None).price_type == PriceType.EXCHANGE_LOCK
    early = choose_bet_price([q(300, 7.0)], OFF, sp=3.0)
    assert early.price_type == PriceType.EXCHANGE_OTHER and early.price == 7.0               # not labelled lock-time
    assert lock_market_state([q(300)], OFF) == "OTHER_ONLY"
    assert choose_bet_price([q(10, 10000.0)], OFF, None).price_type == PriceType.NO_PRICE     # stub bid rejected
    assert choose_bet_price([q(10, 5.0, price_quality="thin_book")], OFF, None).price_type == PriceType.NO_PRICE
    assert choose_bet_price([q(10, 5.0, source_type="BOOKMAKER", is_fallback=True)], OFF, None).price_type == PriceType.NO_PRICE


# ---------------------------------------------------------------- fallback is gap-filling only
def test_fallback_decision_rules(monkeypatch):
    t_in = OFF - timedelta(minutes=10)
    assert not fallback_decision(race_validated=False, primary_lock_state="NONE", now=t_in, off_dt=OFF).allowed
    assert not fallback_decision(race_validated=True, primary_lock_state="LOCK_VALID", now=t_in, off_dt=OFF).allowed   # never overwrite primary
    assert not fallback_decision(race_validated=True, primary_lock_state="NONE", now=OFF + timedelta(minutes=1), off_dt=OFF).allowed  # post-off
    assert not fallback_decision(race_validated=True, primary_lock_state="NONE", now=OFF - timedelta(hours=3), off_dt=OFF).allowed  # window not open
    d = fallback_decision(race_validated=True, primary_lock_state="NONE", now=t_in, off_dt=OFF)
    assert not d.allowed and d.reason == market.NULL_PRIMARY_DOWN                     # ships with NO approved source
    monkeypatch.setitem(market.APPROVED_FALLBACK_SOURCES, "approved-exchange", "EXCHANGE")
    assert fallback_decision(race_validated=True, primary_lock_state="NONE", now=t_in, off_dt=OFF).allowed


def test_same_name_on_separate_disjoint_races_is_not_a_duplicate():
    """Two qualifier heats sharing a sponsor name, hours apart, no common runners: legitimate (17 Oct Pertemps pair)."""
    a = view(1, "a", "13:50:00", "Pertemps Network Handicap Hurdle Race", horses("A", 8), course="Chepstow")
    b = view(2, "b", "15:45:00", "Pertemps Network Handicap Hurdle Race", horses("B", 6), course="Chepstow")
    assert all(r.ok for r in validate_races([a, b], NOW))
    c = view(3, "c", "16:30:00", "Pertemps Network Handicap Hurdle Race", horses("A", 3) + horses("C", 5), course="Chepstow")
    assert not {r.race_id: r for r in validate_races([a, b, c], NOW)}[3].ok          # shares runners => combined/provisional
