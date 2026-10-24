"""Direct retention inventory must pin privacy scope and prior-veto witness."""

from pathlib import Path

import pytest

import ark.personal_context_retention_review as module
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_revocation_continuity_review import review_revocation_continuity
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def _fixture(tmp_path: Path):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 20)
    scope = MemoryScope("local-owner", "private")
    memory.put(MemoryWrite(scope, "fixture", "never export this"))
    ledger = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    ledger.revoke(MemoryScope("other", "private"), at_ms=10)
    return memory, scope, ledger


def _review(state, **kwargs):
    return module.review_synthetic_retention_inventory(
        *state, now_ms=20, **kwargs,
    )


def test_retained_valid_witness_substitution_after_first_veto_denied(
    tmp_path: Path, monkeypatch,
):
    state = _fixture(tmp_path)
    retained = review_revocation_continuity(state[2])
    empty = SyntheticContextRevocationLedger(tmp_path / "empty-veto.sqlite")
    genesis = review_revocation_continuity(empty)
    original = module.review_revocation_continuity
    reads = 0

    def replace_retained(*args, **kwargs):
        nonlocal reads
        result = original(*args, **kwargs)
        reads += 1
        if reads == 1:
            object.__setattr__(retained, "rows", genesis.rows)
            object.__setattr__(retained, "witness_id", genesis.witness_id)
        return result

    monkeypatch.setattr(module, "review_revocation_continuity", replace_retained)
    with pytest.raises(module.SyntheticRetentionRejected, match="retained"):
        _review(state, retained_revocations=retained)
    assert reads == 1


def test_transient_scope_retarget_after_first_veto_denied(tmp_path: Path, monkeypatch):
    state = _fixture(tmp_path)
    original = module.review_revocation_continuity
    memory_reads = 0

    def change_scope(*args, **kwargs):
        result = original(*args, **kwargs)
        object.__setattr__(state[1], "namespace", "other")
        return result

    original_connect = state[0]._connect_readonly

    def restore_scope():
        nonlocal memory_reads
        memory_reads += 1
        object.__setattr__(state[1], "namespace", "private")
        return original_connect()

    monkeypatch.setattr(module, "review_revocation_continuity", change_scope)
    monkeypatch.setattr(state[0], "_connect_readonly", restore_scope)
    with pytest.raises(module.SyntheticRetentionRejected, match="scope"):
        _review(state)
    assert memory_reads == 0


def test_wrong_retained_type_denied_as_privacy_diagnostic(tmp_path: Path):
    with pytest.raises(module.SyntheticRetentionRejected, match="retained"):
        _review(_fixture(tmp_path), retained_revocations=object())


def test_unchanged_retained_evidence_remains_diagnostic(tmp_path: Path):
    state = _fixture(tmp_path)
    receipt = _review(state, retained_revocations=review_revocation_continuity(state[2]))
    assert receipt.revoked is False
    assert len(receipt.items) == 1
    assert receipt.deletion_authorized is False
    assert receipt.erasure_completed is False
    assert receipt.context_use_authorized is False
    assert "never export this" not in repr(receipt)
