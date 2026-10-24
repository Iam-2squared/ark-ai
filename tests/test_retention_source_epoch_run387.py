"""Retention inventory never accepts redirected local Memory or veto sources.

Synthetic, read-only privacy fixtures: these are not erasure or consent proof.
"""

from pathlib import Path

import pytest

import ark.personal_context_retention_review as module
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_retention_review import (
    SyntheticRetentionRejected,
    review_synthetic_retention_inventory,
)
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def _fixture(tmp_path, *, empty=False):
    memory = SQLiteMemoryStore(
        tmp_path / "retention-memory # %.sqlite", clock_ms=lambda: 10,
    )
    scope = MemoryScope("fixture-owner", "private")
    if not empty:
        memory.put(MemoryWrite(scope, "fixture", "private-fixture-data"))
    ledger = SyntheticContextRevocationLedger(tmp_path / "retention-veto.sqlite")
    return memory, scope, ledger


def _review(state):
    return review_synthetic_retention_inventory(
        state[0], state[1], state[2], now_ms=10,
    )


@pytest.mark.parametrize("empty", [False, True])
def test_retention_rejects_memory_source_drift_during_schema(
    tmp_path, monkeypatch, empty,
):
    state = _fixture(tmp_path, empty=empty)
    memory, _scope, _ledger = state
    original_path = memory.path
    original_check = module._validate_v1_schema

    def retarget_after_check(conn):
        original_check(conn)
        memory.path = Path(str(memory.path))

    monkeypatch.setattr(module, "_validate_v1_schema", retarget_after_check)
    with pytest.raises(SyntheticRetentionRejected, match="source changed"):
        _review(state)
    memory.path = original_path
    monkeypatch.setattr(module, "_validate_v1_schema", original_check)
    assert len(_review(state).items) == int(not empty)


@pytest.mark.parametrize("empty", [False, True])
def test_retention_rejects_memory_source_drift_during_open(
    tmp_path, monkeypatch, empty,
):
    state = _fixture(tmp_path, empty=empty)
    memory, _scope, _ledger = state
    original_path = memory.path
    original_open = memory._connect_readonly

    def redirected_open():
        connection = original_open()
        memory.path = Path(str(memory.path))
        return connection

    monkeypatch.setattr(memory, "_connect_readonly", redirected_open)
    with pytest.raises(SyntheticRetentionRejected, match="source changed"):
        _review(state)
    memory.path = original_path
    monkeypatch.setattr(memory, "_connect_readonly", original_open)
    assert len(_review(state).items) == int(not empty)


@pytest.mark.parametrize("after_review", [1, 2])
def test_retention_rejects_revocation_source_drift_at_either_fence(
    tmp_path, monkeypatch, after_review,
):
    state = _fixture(tmp_path)
    _memory, _scope, veto = state
    original_path = veto.path
    original_review = module.review_revocation_continuity
    count = 0

    def redirected_veto(*args, **kwargs):
        nonlocal count
        result = original_review(*args, **kwargs)
        count += 1
        if count == after_review:
            veto.path = Path(str(veto.path))
        return result

    monkeypatch.setattr(module, "review_revocation_continuity", redirected_veto)
    with pytest.raises(SyntheticRetentionRejected, match="source changed"):
        _review(state)
    veto.path = original_path
    monkeypatch.setattr(module, "review_revocation_continuity", original_review)
    assert len(_review(state).items) == 1


def test_retention_review_never_returns_private_content_or_erasure_grant(tmp_path):
    state = _fixture(tmp_path)
    receipt = _review(state)
    assert len(receipt.items) == 1
    assert receipt.context_use_authorized is False
    assert receipt.deletion_authorized is False
    assert receipt.erasure_completed is False
    assert "private-fixture-data" not in repr(receipt)
