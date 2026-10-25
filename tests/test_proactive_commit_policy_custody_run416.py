"""Disconnected trigger preparation must preserve exact policy carriers and durable receipts."""

from pathlib import Path

import pytest

import ark.proactive_synthetic_review as proactive

A = "a" * 64
B = "b" * 64


def _policy(**overrides):
    fields = dict(
        owner="synthetic-owner",
        namespace="fixture",
        definition_id="observe",
        revision=1,
        policy_revision="v1",
        minimum_interval_ms=1,
        rolling_window_ms=10,
        max_preparations_per_window=2,
    )
    fields.update(overrides)
    return proactive.SyntheticTriggerPolicy(**fields)


def _prepare(store, policy, *, now=100):
    return store.prepare(
        policy, source_digest=A, observation_digest=B,
        observed_at_ms=now, now_ms=now,
    )


@pytest.mark.parametrize(
    "field", ("owner", "namespace", "definition_id", "policy_revision"),
)
def test_equal_value_policy_carrier_swap_is_denied_before_sqlite(
    tmp_path: Path, monkeypatch, field,
):
    store = proactive.SyntheticProactiveLedger(tmp_path / "trigger.sqlite")
    policy = _policy()
    original_hash = proactive._hash

    def swapped_hash(label, values):
        if label == "ARK-trigger-scope-v1":
            prior = getattr(policy, field)
            replacement = (" " + prior)[1:]
            assert replacement == prior and replacement is not prior
            object.__setattr__(policy, field, replacement)
        return original_hash(label, values)

    monkeypatch.setattr(proactive, "_hash", swapped_hash)
    with pytest.raises(proactive.SyntheticTriggerRejected, match="policy"):
        _prepare(store, policy)
    assert store.count() == 0


@pytest.mark.parametrize(
    "field", ("owner", "namespace", "definition_id", "policy_revision"),
)
def test_policy_text_budget_is_fail_closed(field):
    with pytest.raises(ValueError, match="budget"):
        _policy(**{field: "x" * 513})
    assert len(getattr(_policy(**{field: "x" * 512}), field)) == 512


def test_post_commit_policy_swap_denies_return_but_preserves_row(
    tmp_path: Path, monkeypatch,
):
    store = proactive.SyntheticProactiveLedger(tmp_path / "trigger.sqlite")
    policy = _policy()
    original_connect = proactive.sqlite3.connect

    class PostCommitConnection:
        def __init__(self, raw):
            self.raw = raw

        def __getattr__(self, name):
            return getattr(self.raw, name)

        def commit(self):
            self.raw.commit()
            previous = policy.namespace
            replacement = (" " + previous)[1:]
            assert replacement == previous and replacement is not previous
            object.__setattr__(policy, "namespace", replacement)

    def connect(*args, **kwargs):
        raw = original_connect(*args, **kwargs)
        if args and "mode=rw" in str(args[0]) and kwargs.get("uri"):
            return PostCommitConnection(raw)
        return raw

    with monkeypatch.context() as scope:
        scope.setattr(proactive.sqlite3, "connect", connect)
        with pytest.raises(proactive.SyntheticTriggerRejected, match="after trigger commit"):
            _prepare(store, policy)
    assert store.count() == 1
    with pytest.raises(proactive.SyntheticTriggerRejected, match="duplicate"):
        _prepare(store, _policy(), now=200)


def test_forged_post_commit_receipt_does_not_erase_durable_reservation(
    tmp_path: Path, monkeypatch,
):
    store = proactive.SyntheticProactiveLedger(tmp_path / "trigger.sqlite")
    original_receipt_type = proactive.SyntheticTriggerReceipt

    def forged_receipt(trigger_id, now_ms):
        return original_receipt_type("trigger_" + "f" * 64, now_ms)

    with monkeypatch.context() as scope:
        scope.setattr(proactive, "SyntheticTriggerReceipt", forged_receipt)
        with pytest.raises(proactive.SyntheticTriggerRejected, match="receipt changed"):
            _prepare(store, _policy())
    assert store.count() == 1
    with pytest.raises(proactive.SyntheticTriggerRejected, match="duplicate"):
        _prepare(store, _policy(), now=200)
