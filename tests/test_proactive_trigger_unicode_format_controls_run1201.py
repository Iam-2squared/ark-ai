"""Run1201: complete Unicode Cf rejection for proactive trigger policies."""

from __future__ import annotations

import pytest

from ark import proactive_synthetic_review as proactive

_FORMAT_CONTROLS = ("\u0600", "\ufff9", "\U000e0001")


def _policy(**overrides: object) -> proactive.SyntheticTriggerPolicy:
    values = {
        "owner": "local-owner",
        "namespace": "private",
        "definition_id": "daily-summary",
        "revision": 1,
        "policy_revision": "policy-v1",
        "minimum_interval_ms": 1,
        "rolling_window_ms": 1000,
        "max_preparations_per_window": 2,
    }
    values.update(overrides)
    return proactive.SyntheticTriggerPolicy(**values)


@pytest.mark.parametrize("control", _FORMAT_CONTROLS)
@pytest.mark.parametrize(
    "field", ("owner", "namespace", "definition_id", "policy_revision"),
)
def test_trigger_policy_rejects_every_unicode_cf(
    control: str, field: str,
) -> None:
    with pytest.raises(ValueError, match="Unicode formatting control"):
        _policy(**{field: "identity" + control})


@pytest.mark.parametrize("control", _FORMAT_CONTROLS)
@pytest.mark.parametrize(
    "field", ("owner", "namespace", "definition_id", "policy_revision"),
)
def test_retained_trigger_policy_revalidates_every_unicode_cf(
    control: str, field: str,
) -> None:
    policy = _policy()
    object.__setattr__(policy, field, "identity" + control)

    with pytest.raises(ValueError, match="Unicode formatting control"):
        policy.identity()


def test_trigger_policy_pins_unicode_category_dependency(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        proactive.unicodedata, "category", lambda _character: "Lo",
    )
    with pytest.raises(
        proactive.SyntheticTriggerRejected,
        match="category classifier changed",
    ):
        _policy()


def test_trigger_policy_pins_unicode_module_identity(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(proactive, "unicodedata", object())
    with pytest.raises(
        proactive.SyntheticTriggerRejected,
        match="category classifier changed",
    ):
        _policy()
