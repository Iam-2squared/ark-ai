"""Preaccess rejection of synthetic proactive receipt descriptor injection.

Receipt hooks are Python code, not merely data. A changed descriptor must
not run even if its getter would return a harmless-looking False.
All data and SQLite writes here are synthetic and disconnected.
"""

from __future__ import annotations

import pytest

from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerReceipt,
    SyntheticTriggerRejected,
)

SOURCE = "a" * 64
OBSERVATION = "b" * 64


def _policy():
    return SyntheticTriggerPolicy(
        owner="fixture", namespace="private", definition_id="local",
        revision=1, policy_revision="v1", minimum_interval_ms=1,
        rolling_window_ms=10, max_preparations_per_window=2,
    )


def _prepare(ledger):
    return ledger.prepare(
        _policy(), source_digest=SOURCE, observation_digest=OBSERVATION,
        observed_at_ms=100, now_ms=100,
    )


@pytest.mark.parametrize(
    "member",
    ("trigger_id", "prepared_at_ms", "__init__", "__getattribute__", "__getattr__"),
)
def test_modified_receipt_descriptor_is_denied_before_sqlite_or_getter(
    tmp_path, monkeypatch, member,
):
    ledger = SyntheticProactiveLedger(tmp_path / "receipt-preaccess.sqlite")
    touched = []

    def dangerous(*_args, **_kwargs):
        touched.append(member)
        raise AssertionError("injected receipt hook was executed")

    with monkeypatch.context() as patch:
        if member in ("trigger_id", "prepared_at_ms"):
            patch.setattr(
                SyntheticTriggerReceipt, member, property(dangerous),
            )
        else:
            # Keep all monkeypatches on the receipt class, never object.
            patch.setattr(
                SyntheticTriggerReceipt, member, dangerous, raising=False,
            )
        with pytest.raises(SyntheticTriggerRejected, match="authority epoch"):
            _prepare(ledger)
        assert touched == []
        assert ledger.count() == 0

    # The unmodified original contract is still usable and remains inert.
    receipt = _prepare(ledger)
    assert ledger.count() == 1
    assert receipt.notification_authorized is False
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert touched == []
