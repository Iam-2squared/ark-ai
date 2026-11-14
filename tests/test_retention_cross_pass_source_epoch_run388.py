"""Cross-pass retention diagnostic rejects reflected source and witness swaps.

Only synthetic Memory/veto evidence is used; nothing is deleted or disclosed.
"""

from pathlib import Path

import pytest

import ark.personal_context_retention_recheck_review as module
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_retention_recheck_review import (
    SyntheticRetentionRecheckRejected,
)
from ark.personal_context_retention_review import review_synthetic_retention_inventory
from ark.personal_context_revocation_continuity_review import review_revocation_continuity
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def _fixture(tmp_path: Path):
    memory = SQLiteMemoryStore(tmp_path / "memory # %.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("offline-owner", "private")
    memory.put(MemoryWrite(scope, "name", "PRIVATE-NOT-FOR-OUTPUT"))
    revocations = SyntheticContextRevocationLedger(tmp_path / "revocations.sqlite")
    cached = review_synthetic_retention_inventory(
        memory, scope, revocations, now_ms=100,
    )
    return memory, scope, revocations, cached


def _review(state, *, retained=None):
    memory, scope, revocations, cached = state
    return module.review_synthetic_retention_recheck(
        memory, scope, revocations, cached,
        now_ms=101, max_age_ms=5, retained_revocations=retained,
    )


@pytest.mark.parametrize("source_index", [0, 2])
@pytest.mark.parametrize("after_pass", [1, 2, 3, 4])
def test_equal_path_replacement_between_inventory_passes_fails_closed(
    tmp_path: Path, monkeypatch, source_index: int, after_pass: int,
):
    state = _fixture(tmp_path)
    original = module.review_synthetic_retention_inventory
    calls = 0

    def injected(*args, **kwargs):
        nonlocal calls
        receipt = original(*args, **kwargs)
        calls += 1
        if calls == after_pass:
            source = state[source_index]
            source.path = Path(str(source.path))
        return receipt

    monkeypatch.setattr(module, "review_synthetic_retention_inventory", injected)
    with pytest.raises(SyntheticRetentionRecheckRejected, match="source"):
        _review(state)
    assert calls == after_pass


@pytest.mark.parametrize("after_pass", [1, 4])
def test_reflected_retained_veto_witness_swap_is_denied(
    tmp_path: Path, monkeypatch, after_pass: int,
):
    state = _fixture(tmp_path)
    witness = review_revocation_continuity(state[2])
    original = module.review_synthetic_retention_inventory
    calls = 0

    def injected(*args, **kwargs):
        nonlocal calls
        receipt = original(*args, **kwargs)
        calls += 1
        if calls == after_pass:
            object.__setattr__(witness, "witness_id", "rvk_" + "f" * 64)
        return receipt

    monkeypatch.setattr(module, "review_synthetic_retention_inventory", injected)
    with pytest.raises(SyntheticRetentionRecheckRejected, match="evidence"):
        _review(state, retained=witness)
    assert calls == after_pass


def test_stable_retained_sources_remain_deny_only(tmp_path: Path):
    state = _fixture(tmp_path)
    receipt = _review(state, retained=review_revocation_continuity(state[2]))
    assert receipt.context_use_authorized is False
    assert receipt.external_disclosure_authorized is False
    assert receipt.deletion_authorized is False
    assert "PRIVATE-NOT-FOR-OUTPUT" not in repr(receipt)
