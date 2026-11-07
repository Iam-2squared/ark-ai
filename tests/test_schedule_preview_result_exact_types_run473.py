"""Detached schedule receipts reject equal-valued but forged cursor carriers."""

from __future__ import annotations

import pytest

import ark.disconnected_schedule_preview as mod


def _inputs(index):
    policy = mod.DisconnectedSchedulePolicy("a" * 64, 10_000, 5_000, 3, 500)
    if index == 0:
        return policy, mod.DisconnectedScheduleCursor(0)
    original = mod.preview_disconnected_schedule(
        policy, mod.DisconnectedScheduleCursor(0), observed_now_ms=10_000,
    )
    return policy, mod.DisconnectedScheduleCursor(1, original.occurrence_id)


@pytest.mark.parametrize(
    ("index", "field", "mutation"),
    (
        (0, "next_index", lambda v: False),
        (1, "next_index", lambda v: True),
        (0, "next_index", lambda v: float(v)),
        (1, "next_index", lambda v: float(v)),
        (0, "due_at_ms", lambda v: float(v)),
        (0, "due_at_ms", lambda v: int(str(v))),
    ),
)
def test_forged_exact_result_numeric_carrier_is_denied(
    monkeypatch, index, field, mutation,
):
    policy, cursor = _inputs(index)
    original_type = mod.DisconnectedDuePreview

    def forged(state, next_index, occurrence_id, due_at_ms, fingerprint):
        fields = dict(
            state=state, next_index=next_index, occurrence_id=occurrence_id,
            due_at_ms=due_at_ms, fingerprint=fingerprint,
        )
        fields[field] = mutation(fields[field])
        return original_type(**fields)

    monkeypatch.setattr(mod, "DisconnectedDuePreview", forged)
    with pytest.raises(mod.SchedulePreviewRejected, match="constructed preview"):
        mod.preview_disconnected_schedule(
            policy, cursor, observed_now_ms=10_000,
        )


def test_unmodified_preview_retains_inert_flags_and_deterministic_digest():
    policy, cursor = _inputs(0)
    a = mod.preview_disconnected_schedule(policy, cursor, observed_now_ms=10_000)
    b = mod.preview_disconnected_schedule(policy, cursor, observed_now_ms=10_000)
    assert a == b
    assert type(a.next_index) is int
    assert type(a.due_at_ms) is int
    assert a.notification_authorized is False
    assert a.tool_execution_authorized is False
    assert a.trusted_clock_verified is False
