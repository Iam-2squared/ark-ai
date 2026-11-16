"""Proactive fixture refuses changed policy descriptors before first field access.

This creates no database and never grants timer, notification, or tool authority.
"""

from __future__ import annotations

import pytest

from ark.proactive_synthetic_review import (
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _policy() -> SyntheticTriggerPolicy:
    return SyntheticTriggerPolicy(
        "local-owner", "private-fixture", "job-one", 1,
        "revision-one", 1_000, 30_000, 2,
    )


@pytest.mark.parametrize(
    "field",
    (
        "owner", "namespace", "definition_id", "revision",
        "policy_revision", "minimum_interval_ms", "rolling_window_ms",
        "max_preparations_per_window", "__getattribute__", "__getattr__",
    ),
)
@pytest.mark.parametrize("entry", ("__post_init__", "identity"))
def test_replaced_field_or_lookup_hook_rejected_before_getter(
    monkeypatch, field: str, entry: str,
) -> None:
    policy = _policy()

    def unexpected(*_args, **_kwargs):
        pytest.fail("unreviewed proactive policy descriptor executed")

    with monkeypatch.context() as patch:
        if field.startswith("__"):
            patch.setattr(
                SyntheticTriggerPolicy, field, unexpected, raising=False,
            )
        else:
            patch.setattr(SyntheticTriggerPolicy, field, property(unexpected))
        # Call through the class, bypassing any hostile instance lookup.
        with pytest.raises(SyntheticTriggerRejected, match="policy contract changed"):
            getattr(SyntheticTriggerPolicy, entry)(policy)
    assert policy.identity()[0] == "local-owner"


def test_original_policy_validation_and_identity_remain_healthy() -> None:
    policy = _policy()
    expected = (
        "local-owner", "private-fixture", "job-one", 1,
        "revision-one", 1_000, 30_000, 2,
    )
    assert policy.identity() == expected
    policy.__post_init__()
