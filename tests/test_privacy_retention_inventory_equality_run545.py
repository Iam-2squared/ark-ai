"""Privacy rechecks must not delegate integrity to patchable dataclass equality."""

from __future__ import annotations

import pytest

import ark.personal_context_retention_recheck_review as review
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_retention_review import (
    SyntheticRetentionInventory,
    review_synthetic_retention_inventory,
)
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def fixture(tmp_path):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "private")
    memory.put(MemoryWrite(
        scope, "source", "SENSITIVE MOCK DATA", expires_at_ms=101,
    ))
    veto = SyntheticContextRevocationLedger(tmp_path / "revocations.sqlite")
    captured = review_synthetic_retention_inventory(
        memory, scope, veto, now_ms=100,
    )
    return memory, scope, veto, captured


def recheck(state):
    return review.review_synthetic_retention_recheck(
        *state, now_ms=101, max_age_ms=10,
    )


@pytest.mark.parametrize("phase", (1, 3, 4))
def test_true_dataclass_equality_cannot_hide_stale_privacy_inventory(
    tmp_path, monkeypatch, phase,
):
    state = fixture(tmp_path)
    real_review = review.review_synthetic_retention_inventory
    count = 0

    def forged_review(*args, **kwargs):
        nonlocal count
        returned = real_review(*args, **kwargs)
        count += 1
        if count == phase:
            object.__setattr__(
                returned, "inventory_digest", "retention_" + "f" * 64,
            )
        return returned

    monkeypatch.setattr(
        SyntheticRetentionInventory, "__eq__", lambda self, other: True,
    )
    monkeypatch.setattr(
        review, "review_synthetic_retention_inventory", forged_review,
    )
    with pytest.raises(review.SyntheticRetentionRecheckRejected, match="changed|drifted"):
        recheck(state)
    assert count == phase if phase == 1 else count == 4


def test_false_dataclass_equality_cannot_reject_unchanged_privacy_evidence(
    tmp_path, monkeypatch,
):
    state = fixture(tmp_path)
    monkeypatch.setattr(
        SyntheticRetentionInventory, "__eq__", lambda self, other: False,
    )
    result = recheck(state)
    assert len(result.expired_memory_ids) == 1
    assert result.deletion_authorized is False
    assert result.erasure_completed is False
    assert result.external_disclosure_authorized is False


def test_valid_inventory_review_is_read_only_and_excludes_private_content(tmp_path):
    state = fixture(tmp_path)
    result = recheck(state)
    assert result.scope_digest == state[3].scope_digest
    assert "SENSITIVE MOCK DATA" not in repr(result)
    assert result.context_use_authorized is False
