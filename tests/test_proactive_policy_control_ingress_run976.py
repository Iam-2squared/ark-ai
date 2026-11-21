"""Synthetic proactive policy identities are unambiguous before SQLite.

No real scheduler, notifications, trusted clock, consent or tool execution.
Only a local fixture ledger is used for admission/restart checks.
"""

from __future__ import annotations

import pytest

from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
)


def _policy(**overrides: object) -> SyntheticTriggerPolicy:
    fields = {
        "owner": "所有者",
        "namespace": "private",
        "definition_id": "予定🧪",
        "revision": 1,
        "policy_revision": "改訂",
        "minimum_interval_ms": 1,
        "rolling_window_ms": 1000,
        "max_preparations_per_window": 2,
    }
    fields.update(overrides)
    return SyntheticTriggerPolicy(**fields)


@pytest.mark.parametrize(
    ("control", "diagnostic"),
    (
        ("\n", "ASCII control"),
        ("\t", "ASCII control"),
        ("\x7f", "ASCII control"),
        ("\u009b", "Unicode formatting control"),
        ("\u202e", "Unicode formatting control"),
        ("\u200b", "Unicode formatting control"),
        ("\u2028", "Unicode formatting control"),
        ("\ufeff", "Unicode formatting control"),
    ),
)
@pytest.mark.parametrize(
    "field", ("owner", "namespace", "definition_id", "policy_revision"),
)
def test_proactive_policy_rejects_spoofed_identity_before_persistence(
    control: str, diagnostic: str, field: str,
) -> None:
    with pytest.raises(ValueError, match=diagnostic):
        _policy(**{field: "local" + control + "forged"})


@pytest.mark.parametrize(
    "field", ("owner", "namespace", "definition_id", "policy_revision"),
)
@pytest.mark.parametrize("control", ("\x1b", "\u2066"))
def test_reflected_policy_identity_denied_before_fixture_write(
    tmp_path, field: str, control: str,
) -> None:
    ledger = SyntheticProactiveLedger(tmp_path / "inert-trigger.sqlite")
    policy = _policy()
    object.__setattr__(policy, field, "synthetic" + control + "forged")
    with pytest.raises(ValueError, match="control"):
        ledger.prepare(
            policy,
            source_digest="a" * 64,
            observation_digest="b" * 64,
            observed_at_ms=20,
            now_ms=20,
        )
    assert ledger.count() == 0


def test_clean_multilingual_policy_still_creates_only_inert_marker(tmp_path) -> None:
    ledger = SyntheticProactiveLedger(tmp_path / "inert-trigger.sqlite")
    receipt = ledger.prepare(
        _policy(),
        source_digest="a" * 64,
        observation_digest="b" * 64,
        observed_at_ms=20,
        now_ms=20,
    )
    assert receipt.trigger_id.startswith("trigger_")
    assert receipt.notification_authorized is False
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert ledger.count() == 1
