"""Synthetic proactive policy identifiers reject NUL before persistence.

No scheduler, notification, real clock, consent, or external action is enabled.
"""

from dataclasses import replace

import pytest

from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
)


def _policy() -> SyntheticTriggerPolicy:
    return SyntheticTriggerPolicy(
        "fixture-owner", "private", "fixture-definition", 1,
        "policy-v1", 100, 1000, 5,
    )


@pytest.mark.parametrize(
    "field", ("owner", "namespace", "definition_id", "policy_revision"),
)
@pytest.mark.parametrize(
    "value", ("\x00fixture", "fixture\x00identity", "fixture\x00"),
)
def test_synthetic_policy_nul_text_is_rejected_before_store(
    field: str, value: str, tmp_path,
) -> None:
    path = tmp_path / "must-not-be-created.sqlite3"
    with pytest.raises(ValueError, match="NUL separator"):
        replace(_policy(), **{field: value})
    assert not path.exists()


def test_valid_unicode_policy_remains_local_and_deny_only(tmp_path) -> None:
    policy = replace(_policy(), owner="fixture-owner-地域")
    assert policy.identity()[0] == "fixture-owner-地域"
    ledger = SyntheticProactiveLedger(tmp_path / "prepared.sqlite3")
    receipt = ledger.prepare(
        policy, source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=900, now_ms=1000,
    )
    assert receipt.notification_authorized is False
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert ledger.count() == 1
