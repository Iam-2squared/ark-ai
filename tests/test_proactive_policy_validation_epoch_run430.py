"""Direct proactive policy identity must preserve original field carriers.

No real notification, clock attestation, ToolBackend or scheduler worker is
used. Reentrant validator callbacks are synthetic, local test hooks only.
"""

import pytest

import ark.proactive_synthetic_review as proactive


def _policy():
    return proactive.SyntheticTriggerPolicy(
        "owner-for-offline-fixture", "private", "observe", 1,
        "synthetic-revision-v1", 2, 10, 3,
    )


def _equal_clone(value):
    duplicate = (" " + value)[1:]
    assert duplicate == value and duplicate is not value
    return duplicate


@pytest.mark.parametrize("replacement", ("equal_carrier", "changed_value"))
def test_text_validation_cannot_temporarily_retarget_policy_identity(
    monkeypatch, replacement,
):
    policy = _policy()
    native = proactive._text
    entered = []

    def reentrant_text(name, value):
        native(name, value)
        if name == "owner":
            entered.append(True)
            if replacement == "equal_carrier":
                object.__setattr__(
                    policy, "policy_revision", _equal_clone(policy.policy_revision),
                )
            else:
                object.__setattr__(policy, "namespace", "different-private")
        elif name == "namespace":
            # An end-only check would miss a mutation restored in this hook.
            object.__setattr__(policy, "namespace", "private")

    monkeypatch.setattr(proactive, "_text", reentrant_text)
    with pytest.raises(ValueError, match="policy changed during validation"):
        policy.identity()
    assert entered == [True]


@pytest.mark.parametrize("field", ("minimum_interval_ms", "max_preparations_per_window"))
def test_integer_validation_cannot_temporarily_retarget_policy(
    monkeypatch, field,
):
    policy = _policy()
    native = proactive._int
    entered = []

    def reentrant_int(name, value, *, minimum=0):
        native(name, value, minimum=minimum)
        if name == "revision":
            entered.append(True)
            object.__setattr__(policy, field, getattr(policy, field) + 1)
        elif name == "minimum_interval_ms":
            object.__setattr__(policy, field, 2 if field == name else 3)

    monkeypatch.setattr(proactive, "_int", reentrant_int)
    with pytest.raises(ValueError, match="policy changed during validation"):
        policy.identity()
    assert entered == [True]


def test_unmodified_policy_identity_is_stable_and_local():
    policy = _policy()
    expected = (
        "owner-for-offline-fixture", "private", "observe", 1,
        "synthetic-revision-v1", 2, 10, 3,
    )
    assert policy.identity() == expected
    assert policy.identity() == expected
