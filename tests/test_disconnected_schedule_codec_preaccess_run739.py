"""Run739: detached recurrence codec/custody stays deny-only, before private data."""

import re
from types import SimpleNamespace

import pytest

from ark import disconnected_schedule_preview as mod


def policy():
    return mod.DisconnectedSchedulePolicy("a" * 64, 1000, 2000, 2, 200)


@pytest.mark.parametrize("field,value", [
    ("_MAX_MS", 2**63),
    ("_MAX_MS", True),
    ("_MAX_COUNT", 4097),
    ("_MAX_COUNT", 0),
    ("_MAX_INTERVAL_MS", 366 * 24 * 60 * 60 * 1000 + 1),
    ("_MAX_GRACE_MS", 60_001),
    ("_SHA", re.compile(r".*")),
    ("_OCCURRENCE", re.compile(r".*")),
    ("_DOMAIN", b"unreviewed-clock-domain"),
])
def test_deny_changed_recurrence_protocol_before_processing(monkeypatch, field, value):
    monkeypatch.setattr(mod, field, value)
    with pytest.raises(mod.SchedulePreviewRejected, match="changed"):
        mod.preview_disconnected_schedule(
            policy(), mod.DisconnectedScheduleCursor(0), observed_now_ms=1000,
        )


@pytest.mark.parametrize("field,value", [
    ("hashlib", SimpleNamespace(sha256=lambda *_: (_ for _ in ()).throw(
        AssertionError("SHA callback was invoked")
    ))),
    ("json", SimpleNamespace(dumps=lambda *_args, **_kw: (_ for _ in ()).throw(
        AssertionError("JSON callback was invoked")
    ))),
])
def test_reject_replaced_codec_without_calling_untrusted_code(monkeypatch, field, value):
    monkeypatch.setattr(mod, field, value)
    with pytest.raises(mod.SchedulePreviewRejected, match="changed"):
        mod.preview_disconnected_schedule(
            policy(), mod.DisconnectedScheduleCursor(0), observed_now_ms=1000,
        )


def test_deterministic_non_authoritative_recurrence():
    p = policy()
    cursor = mod.DisconnectedScheduleCursor(0)
    due = mod.preview_disconnected_schedule(p, cursor, observed_now_ms=1000)
    assert due == mod.preview_disconnected_schedule(p, cursor, observed_now_ms=1000)
    assert due.state == "DUE_UNVERIFIED"
    assert due.occurrence_id and due.occurrence_id.startswith("slot_")
    assert len(due.fingerprint) == 64
    assert not due.trusted_clock_verified
    assert not due.notification_authorized
    assert not due.tool_execution_authorized
    assert not due.automatic_replay_authorized
    assert not due.consent_verified

    last = mod.DisconnectedScheduleCursor(1, due.occurrence_id)
    expired = mod.preview_disconnected_schedule(p, last, observed_now_ms=4000)
    assert expired.state == "EXPIRED_QUARANTINE"
    assert expired.next_index == 1
    exhausted = mod.preview_disconnected_schedule(
        p, mod.DisconnectedScheduleCursor(2, expired.occurrence_id),
        observed_now_ms=5000,
    )
    assert exhausted.state == "EXHAUSTED"
    assert exhausted.occurrence_id is None


def test_synthetic_clock_outside_grace_cannot_advance_cursor():
    snapshot = mod.preview_disconnected_schedule(
        policy(), mod.DisconnectedScheduleCursor(0), observed_now_ms=1201,
    )
    assert snapshot.state == "EXPIRED_QUARANTINE"
    assert snapshot.next_index == 0
