"""Run978: deny-only recurrence control vectors retain exact import identity.

Synthetic identifiers only; no clocks, timers, notifications, persistence,
user data, model execution, or external action authorization.
"""

from __future__ import annotations

import pytest

from ark import disconnected_schedule_preview as mod


def _preview():
    policy = mod.DisconnectedSchedulePolicy("a" * 64, 10_000, 5_000, 3, 500)
    cursor = mod.DisconnectedScheduleCursor(0)
    return mod.preview_disconnected_schedule(
        policy, cursor, observed_now_ms=10_000,
    )


@pytest.mark.parametrize("name", [
    "_CARRIER_FIELDS",
    "_CARRIER_HOOKS",
    "_DENIAL_NAMES",
    "_ORIGINAL_CARRIER_DESCRIPTORS",
    "_ORIGINAL_DENIAL_DESCRIPTORS",
])
@pytest.mark.parametrize("replacement", ["same_values_new_tuple", "truncated"])
def test_rebound_control_vector_denied_before_synthetic_occurrence(
    name, replacement, monkeypatch,
):
    healthy = _preview()
    assert healthy.notification_authorized is False
    original = getattr(mod, name)
    if replacement == "same_values_new_tuple":
        substitute = tuple(list(original))
        assert substitute == original
        assert substitute is not original
    else:
        substitute = original[:-1]

    calls = []

    def forbidden_occurrence(*_args, **_kwargs):
        calls.append("unreviewed occurrence")
        pytest.fail("unreviewed occurrence callback executed")

    with monkeypatch.context() as patch:
        patch.setattr(mod, name, substitute)
        patch.setattr(mod, "_occurrence", forbidden_occurrence)
        with pytest.raises(
            mod.SchedulePreviewRejected, match="constructed preview carrier changed",
        ):
            _preview()
    assert calls == []
    assert _preview().fingerprint == healthy.fingerprint


def test_original_schedule_preview_retains_deny_only_flags():
    result = _preview()
    assert result.state == "DUE_UNVERIFIED"
    assert result.trusted_clock_verified is False
    assert result.notification_authorized is False
    assert result.tool_execution_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.consent_verified is False
