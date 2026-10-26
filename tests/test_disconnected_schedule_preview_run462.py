"""Synthetic recurring scheduler previews must never become runtime grants."""

from dataclasses import FrozenInstanceError

import pytest

from ark.disconnected_schedule_preview import (
    DisconnectedDuePreview,
    DisconnectedScheduleCursor,
    DisconnectedSchedulePolicy,
    SchedulePreviewRejected,
    preview_disconnected_schedule,
)


def _policy(**changes):
    kw = dict(policy_sha256="a" * 64, first_due_at_ms=10_000,
              interval_ms=5_000, occurrence_count=3, grace_ms=500)
    kw.update(changes)
    return DisconnectedSchedulePolicy(**kw)


def _preview(policy=None, cursor=None, now=10_000):
    return preview_disconnected_schedule(
        policy or _policy(), cursor or DisconnectedScheduleCursor(0),
        observed_now_ms=now,
    )


def test_due_at_edge_and_grace():
    assert _preview(now=9_999).state == "NOT_DUE"
    assert _preview(now=10_000).state == "DUE_UNVERIFIED"
    assert _preview(now=10_500).state == "DUE_UNVERIFIED"
    assert _preview(now=10_501).state == "EXPIRED_QUARANTINE"


def test_no_skips_or_catchup_even_when_multiple_periods_elapsed():
    p = _policy()
    old = _preview(now=20_000)
    assert old.next_index == 0
    assert old.state == "EXPIRED_QUARANTINE"
    one = _preview(p, DisconnectedScheduleCursor(1, old.occurrence_id), 20_000)
    assert one.state == "EXPIRED_QUARANTINE"
    assert one.due_at_ms == 15_000
    two = _preview(p, DisconnectedScheduleCursor(2, one.occurrence_id), 20_000)
    assert two.state == "DUE_UNVERIFIED"
    assert two.due_at_ms == 20_000
    exhausted = _preview(p, DisconnectedScheduleCursor(3, two.occurrence_id), 30_000)
    assert exhausted.state == "EXHAUSTED"
    assert exhausted.due_at_ms is None
    assert exhausted.occurrence_id is None


def test_no_execution_consent_or_trusted_clock():
    result = _preview()
    assert result.trusted_clock_verified is False
    assert result.notification_authorized is False
    assert result.tool_execution_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.consent_verified is False
    assert "slot_" not in repr(result)


def test_deterministic_policy_binding():
    a = _preview()
    assert a == _preview()
    assert a.fingerprint != _preview(now=10_001).fingerprint
    assert a.occurrence_id != _preview(_policy(policy_sha256="b" * 64)).occurrence_id
    assert a.occurrence_id != _preview(_policy(first_due_at_ms=11_000), now=11_000).occurrence_id


def test_prior_cursor_bind_fails_for_other_policy_and_forged_id():
    first = _preview()
    bad = DisconnectedScheduleCursor(1, first.occurrence_id)
    with pytest.raises(SchedulePreviewRejected, match="prior occurrence"):
        _preview(_policy(policy_sha256="b" * 64), bad)
    with pytest.raises(SchedulePreviewRejected, match="prior occurrence"):
        _preview(cursor=DisconnectedScheduleCursor(1, "slot_" + "f" * 64))


@pytest.mark.parametrize("policy", [
    _policy(policy_sha256="A" * 64),
    _policy(policy_sha256="x" * 64),
    _policy(first_due_at_ms=True),
    _policy(first_due_at_ms=-1),
    _policy(first_due_at_ms=2**63),
    _policy(interval_ms=999),
    _policy(interval_ms=2**63),
    _policy(interval_ms=True),
    _policy(occurrence_count=0),
    _policy(occurrence_count=4097),
    _policy(occurrence_count=1.0),
    _policy(grace_ms=-1),
    _policy(grace_ms=5000),
    _policy(grace_ms=60_001),
    _policy(first_due_at_ms=2**63 - 200, interval_ms=1000),
])
def test_invalid_policy_rejected(policy):
    with pytest.raises(SchedulePreviewRejected):
        _preview(policy)


@pytest.mark.parametrize("cursor", [
    DisconnectedScheduleCursor(-1),
    DisconnectedScheduleCursor(True),
    DisconnectedScheduleCursor(4),
    DisconnectedScheduleCursor(0, "slot_" + "0" * 64),
    DisconnectedScheduleCursor(1),
    DisconnectedScheduleCursor(1, "invalid"),
])
def test_bad_cursor_rejected(cursor):
    with pytest.raises(SchedulePreviewRejected):
        _preview(cursor=cursor)


@pytest.mark.parametrize("now", [-1, True, 1.0, 2**63, None])
def test_untrusted_bad_clock_rejected(now):
    with pytest.raises(SchedulePreviewRejected):
        _preview(now=now)


def test_frozen_values():
    first = _preview()
    with pytest.raises(FrozenInstanceError):
        first.state = "APPROVED"
    with pytest.raises(FrozenInstanceError):
        _policy().interval_ms = 1


def test_exact_subtypes_required():
    class DerivedPolicy(DisconnectedSchedulePolicy):
        pass
    with pytest.raises(SchedulePreviewRejected):
        _preview(policy=DerivedPolicy("a" * 64, 10_000, 5_000, 3, 500))
    with pytest.raises(SchedulePreviewRejected):
        preview_disconnected_schedule(_policy(), {}, observed_now_ms=10_000)


def test_no_unbounded_result():
    p = _policy(first_due_at_ms=2**63 - 1, interval_ms=1000,
                occurrence_count=1, grace_ms=0)
    assert _preview(p, now=2**63 - 1).state == "DUE_UNVERIFIED"
    assert _preview(p, now=0).state == "NOT_DUE"


def test_digest_changes_with_cursor():
    p = _policy()
    first = _preview(p)
    later = _preview(p, DisconnectedScheduleCursor(1, first.occurrence_id), 15_000)
    assert later.fingerprint != first.fingerprint
    assert len(later.fingerprint) == 64
    assert isinstance(later, DisconnectedDuePreview)
