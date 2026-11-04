"""COMMITTED offline trigger receipts cannot become authority via a property.

The fixture stores a local deduplication marker, not a notification or a
real-world action. Rejection after COMMIT must not be treated as rollback.
"""

import pytest

import ark.proactive_synthetic_review as module


def _prepare(tmp_path):
    ledger = module.SyntheticProactiveLedger(tmp_path / "receipt-epoch.sqlite")
    policy = module.SyntheticTriggerPolicy(
        "offline", "fixture", "reminder", 1, "policy-v1", 5, 50, 3,
    )

    def submit():
        return ledger.prepare(
            policy, source_digest="a" * 64, observation_digest="b" * 64,
            observed_at_ms=90, now_ms=100,
        )

    return ledger, submit


@pytest.mark.parametrize("field", module._RECEIPT_DENIALS)
def test_false_only_replacement_is_not_original_receipt_authority(
    tmp_path, monkeypatch, field,
):
    ledger, submit = _prepare(tmp_path)
    monkeypatch.setattr(
        module.SyntheticTriggerReceipt, field, property(lambda _: False),
    )
    with pytest.raises(module.SyntheticTriggerRejected, match="authority epoch"):
        submit()
    # The denial runs AFTER the local COMMIT. No blind automatic retry.
    assert ledger.count() == 1


@pytest.mark.parametrize("field", module._RECEIPT_DENIALS)
def test_receipt_cannot_claim_real_notification_or_dispatch(
    tmp_path, monkeypatch, field,
):
    ledger, submit = _prepare(tmp_path)
    monkeypatch.setattr(
        module.SyntheticTriggerReceipt, field, property(lambda _: True),
    )
    with pytest.raises(module.SyntheticTriggerRejected, match="gained authority|authority epoch changed"):
        submit()
    assert ledger.count() == 1


def test_reentrant_denial_cannot_rebase_earlier_original_descriptor(
    tmp_path, monkeypatch,
):
    ledger, submit = _prepare(tmp_path)
    receipt_type = module.SyntheticTriggerReceipt
    original = receipt_type.__getattribute__
    triggered = []

    def late_replacement(self, name):
        result = original(self, name)
        if name == "automatic_replay_authorized":
            triggered.append(name)
            monkeypatch.setattr(
                receipt_type, "notification_authorized",
                property(lambda _: False),
            )
        return result

    monkeypatch.setattr(receipt_type, "__getattribute__", late_replacement)
    with pytest.raises(module.SyntheticTriggerRejected, match="authority epoch"):
        submit()
    assert triggered == ["automatic_replay_authorized"]
    assert ledger.count() == 1


def test_deny_getter_cannot_modify_committed_receipt_carrier(
    tmp_path, monkeypatch,
):
    ledger, submit = _prepare(tmp_path)
    receipt_type = module.SyntheticTriggerReceipt
    original = receipt_type.__getattribute__

    def drift(self, name):
        result = original(self, name)
        if name == "automatic_replay_authorized":
            old = original(self, "trigger_id")
            copy = ("!" + old)[1:]
            assert copy == old and copy is not old
            object.__setattr__(self, "trigger_id", copy)
        return result

    monkeypatch.setattr(receipt_type, "__getattribute__", drift)
    with pytest.raises(module.SyntheticTriggerRejected, match="receipt changed"):
        submit()
    assert ledger.count() == 1


def test_unmodified_receipt_is_exact_and_never_authorizes(tmp_path):
    ledger, submit = _prepare(tmp_path)
    receipt = submit()
    assert type(receipt) is module.SyntheticTriggerReceipt
    assert receipt.notification_authorized is False
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert ledger.count() == 1
