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
    # Ingress rejects tampered descriptors before any SQLite write.
    assert ledger.count() == 0


@pytest.mark.parametrize("field", module._RECEIPT_DENIALS)
def test_receipt_cannot_claim_real_notification_or_dispatch(
    tmp_path, monkeypatch, field,
):
    ledger, submit = _prepare(tmp_path)
    monkeypatch.setattr(
        module.SyntheticTriggerReceipt, field, property(lambda _: True),
    )
    with pytest.raises(
        module.SyntheticTriggerRejected,
        match="gained authority|authority epoch changed",
    ):
        submit()
    assert ledger.count() == 0


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
    assert triggered == []
    assert ledger.count() == 0


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
    with pytest.raises(module.SyntheticTriggerRejected, match="authority epoch"):
        submit()
    assert ledger.count() == 0


def test_unmodified_receipt_is_exact_and_never_authorizes(tmp_path):
    ledger, submit = _prepare(tmp_path)
    receipt = submit()
    assert type(receipt) is module.SyntheticTriggerReceipt
    assert receipt.notification_authorized is False
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert ledger.count() == 1


def test_post_commit_descriptor_drift_is_reported_without_erasing_marker(
    tmp_path, monkeypatch,
):
    ledger, submit = _prepare(tmp_path)
    original_connect = module.sqlite3.connect

    class DriftAfterCommit:
        def __init__(self, raw):
            self.raw = raw

        def __getattr__(self, name):
            return getattr(self.raw, name)

        def commit(self):
            self.raw.commit()
            # Tamper only AFTER the real SQLite COMMIT. Preaccess validation
            # cannot predict this; the durable marker must not be forgotten.
            scope.setattr(
                module.SyntheticTriggerReceipt, "notification_authorized",
                property(lambda _: False),
            )

    def connect(*args, **kwargs):
        raw = original_connect(*args, **kwargs)
        if args and "mode=rw" in str(args[0]) and kwargs.get("uri"):
            return DriftAfterCommit(raw)
        return raw

    with monkeypatch.context() as scope:
        scope.setattr(module.sqlite3, "connect", connect)
        with pytest.raises(module.SyntheticTriggerRejected, match="authority epoch"):
            submit()
    assert ledger.count() == 1
    # Advance beyond the minimum-interval fence while retaining the SAME
    # source/observation occurrence. Only the stored primary key can now
    # reject the replay, proving the marker survived the failed return.
    with pytest.raises(module.SyntheticTriggerRejected, match="duplicate"):
        ledger.prepare(
            module.SyntheticTriggerPolicy(
                "offline", "fixture", "reminder", 1, "policy-v1", 5, 50, 3,
            ),
            source_digest="a" * 64, observation_digest="b" * 64,
            observed_at_ms=100, now_ms=105,
        )
    assert ledger.count() == 1
