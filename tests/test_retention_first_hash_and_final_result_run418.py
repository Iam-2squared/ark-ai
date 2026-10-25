"""Offline retention inventory cannot silently rebase earliest or final epochs.

All fixtures are disconnected and content-minimized. No consent, erasure,
external notification or authorization is inferred from the local digest.
"""

from pathlib import Path

import pytest

import ark.personal_context_retention_review as review
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def _state(tmp_path):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "private-scope")
    memory.put(MemoryWrite(scope, "fixture", "LOCAL PRIVATE FIXTURE"))
    ledger = SyntheticContextRevocationLedger(tmp_path / "privacy.sqlite")
    return memory, scope, ledger


def _equal_carrier(value: str) -> str:
    other = ("~" + value)[1:]
    assert other == value and other is not value
    return other


def _mutate(state, target, *, equal=False):
    memory, scope, ledger = state
    if target == "memory_path":
        memory.path = Path(str(memory.path))
    elif target == "veto_path":
        ledger.path = Path(str(ledger.path))
    elif target == "owner":
        object.__setattr__(
            scope, "owner_id",
            _equal_carrier(scope.owner_id) if equal else "new-owner",
        )
    elif target == "namespace":
        object.__setattr__(
            scope, "namespace",
            _equal_carrier(scope.namespace) if equal else "new-namespace",
        )
    else:
        raise AssertionError(target)


@pytest.mark.parametrize(
    "target", ("memory_path", "veto_path", "owner", "namespace"),
)
def test_first_scope_hash_cannot_rebase_unpinned_inputs(
    tmp_path, monkeypatch, target,
):
    state = _state(tmp_path)
    original = review._scope_digest
    calls = 0

    def hostile_scope_hash(scope):
        nonlocal calls
        calls += 1
        _mutate(state, target, equal=True)
        return original(scope)

    monkeypatch.setattr(review, "_scope_digest", hostile_scope_hash)
    with pytest.raises(review.SyntheticRetentionRejected, match="changed"):
        review.review_synthetic_retention_inventory(
            *state, now_ms=100,
        )
    assert calls == 1


@pytest.mark.parametrize(
    "target", ("memory_path", "veto_path", "owner", "namespace"),
)
def test_final_hash_callback_cannot_retarget_inventory_inputs(
    tmp_path, monkeypatch, target,
):
    state = _state(tmp_path)
    original_sha256 = review.hashlib.sha256
    callbacks = 0

    class FinalDigest:
        def __init__(self, wrapped):
            self.wrapped = wrapped

        def hexdigest(self):
            nonlocal callbacks
            callbacks += 1
            _mutate(state, target, equal=True)
            return self.wrapped.hexdigest()

    def hostile_sha256(data=b"", *args, **kwargs):
        wrapped = original_sha256(data, *args, **kwargs)
        if (
            type(data) is bytes
            and data.startswith(b'["ARK-offline-retention-inventory-v2"')
        ):
            return FinalDigest(wrapped)
        return wrapped

    monkeypatch.setattr(review.hashlib, "sha256", hostile_sha256)
    with pytest.raises(review.SyntheticRetentionRejected, match="changed"):
        review.review_synthetic_retention_inventory(*state, now_ms=100)
    assert callbacks == 1


def test_constructed_inventory_does_not_escape_with_rewritten_item(
    tmp_path, monkeypatch,
):
    state = _state(tmp_path)
    original = review.SyntheticRetentionInventory.__init__
    constructions = 0

    def hostile_construct(self, *args, **kwargs):
        nonlocal constructions
        original(self, *args, **kwargs)
        constructions += 1
        object.__setattr__(self.items[0], "revision", 777)

    monkeypatch.setattr(
        review.SyntheticRetentionInventory, "__init__", hostile_construct,
    )
    with pytest.raises(
        review.SyntheticRetentionRejected,
        match="retention inventory items changed",
    ):
        review.review_synthetic_retention_inventory(*state, now_ms=100)
    assert constructions == 1


def test_stable_retention_digest_is_deterministic_and_inert(tmp_path):
    state = _state(tmp_path)
    first = review.review_synthetic_retention_inventory(*state, now_ms=100)
    assert first == review.review_synthetic_retention_inventory(*state, now_ms=100)
    assert first.inventory_digest.startswith("retention_")
    assert len(first.items) == 1
    assert not first.context_use_authorized
    assert not first.deletion_authorized
    assert not first.erasure_completed
    assert "LOCAL PRIVATE FIXTURE" not in repr(first)
