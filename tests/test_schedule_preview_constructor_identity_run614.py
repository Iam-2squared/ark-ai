"""Offline scheduler refuses rebound classes before synthetic execution.

These tests do not use an OS clock, notify anyone, or dispatch a tool.
"""

from __future__ import annotations

import pytest

from ark import disconnected_schedule_preview as schedule


def _inputs():
    policy = schedule._POLICY_TYPE("a" * 64, 10_000, 5_000, 3, 500)
    cursor = schedule._CURSOR_TYPE(0)
    return policy, cursor


@pytest.mark.parametrize(
    "name",
    ("DisconnectedSchedulePolicy", "DisconnectedScheduleCursor"),
)
def test_rebound_input_class_rejected_before_policy_validation(
    monkeypatch: pytest.MonkeyPatch, name: str,
) -> None:
    policy, cursor = _inputs()
    original = getattr(schedule, name)
    monkeypatch.setattr(schedule, name, type("Counterfeit", (original,), {}))
    with pytest.raises(schedule.SchedulePreviewRejected, match="carrier changed"):
        schedule.preview_disconnected_schedule(
            policy, cursor, observed_now_ms=10_000,
        )


def test_rebound_output_constructor_never_executes(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy, cursor = _inputs()
    calls = []

    def fake_result(*args):
        calls.append(args)
        return object()

    monkeypatch.setattr(schedule, "DisconnectedDuePreview", fake_result)
    with pytest.raises(schedule.SchedulePreviewRejected, match="carrier changed"):
        schedule.preview_disconnected_schedule(
            policy, cursor, observed_now_ms=10_000,
        )
    assert calls == []


def test_hash_callback_cannot_rebind_result_constructor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy, cursor = _inputs()
    calls = []
    original_sha256 = schedule.hashlib.sha256

    def fake_result(*args):
        calls.append(args)
        return object()

    def mutate_before_result(*args, **kwargs):
        monkeypatch.setattr(schedule, "DisconnectedDuePreview", fake_result)
        return original_sha256(*args, **kwargs)

    monkeypatch.setattr(schedule.hashlib, "sha256", mutate_before_result)
    with pytest.raises(schedule.SchedulePreviewRejected, match="carrier changed"):
        schedule.preview_disconnected_schedule(
            policy, cursor, observed_now_ms=10_000,
        )
    assert calls == []


def test_unmodified_preview_is_not_a_dispatch_grant() -> None:
    policy, cursor = _inputs()
    preview = schedule.preview_disconnected_schedule(
        policy, cursor, observed_now_ms=10_000,
    )
    assert type(preview) is schedule._RESULT_TYPE
    assert preview.state == "DUE_UNVERIFIED"
    for name in schedule._DENIAL_NAMES:
        assert getattr(preview, name) is False
