"""Privacy retention result remains diagnostic after final denied getter.

The synthetic Memory fixture never grants context disclosure, export, purge,
forensic erasure, or external execution.
"""

from pathlib import Path

import pytest

from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_retention_review import (
    RetentionState,
    SyntheticRetentionInventory,
    SyntheticRetentionRejected,
    review_synthetic_retention_inventory,
)
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def build(tmp_path):
    memory = SQLiteMemoryStore(
        tmp_path / "memory.sqlite", clock_ms=lambda: 100,
    )
    scope = MemoryScope("synthetic-owner", "private-profile")
    memory.put(MemoryWrite(
        scope, "synthetic-source", "LOCAL PRIVATE FIXTURE",
        expires_at_ms=101,
    ))
    veto = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    return memory, scope, veto


def invoke(state):
    return review_synthetic_retention_inventory(*state, now_ms=100)


def test_valid_inventory_remains_content_minimized_and_denied(tmp_path):
    state = build(tmp_path)
    result = invoke(state)
    assert result.expired_count == 0
    assert result.items[0].state is RetentionState.NOT_EXPIRED
    assert result.erasure_completed is False
    assert result.deletion_authorized is False
    assert result.context_use_authorized is False
    assert "LOCAL PRIVATE FIXTURE" not in repr(result)


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("scope_digest", "f" * 64),
        ("inventory_digest", "retention_" + "f" * 64),
        ("reviewed_at_ms", 200),
        ("revoked", True),
        ("items", ()),
    ),
)
def test_last_false_authority_getter_cannot_replace_result(
    tmp_path, monkeypatch, field, replacement,
):
    state = build(tmp_path)

    def mutation(self):
        object.__setattr__(self, field, replacement)
        return False

    monkeypatch.setattr(
        SyntheticRetentionInventory, "context_use_authorized",
        property(mutation),
    )
    with pytest.raises(SyntheticRetentionRejected, match="authority denial"):
        invoke(state)


@pytest.mark.parametrize(
    "target",
    ("item_revision", "item_state", "owner", "memory_path", "veto_path"),
)
def test_last_false_authority_getter_cannot_replace_original_evidence(
    tmp_path, monkeypatch, target,
):
    state = build(tmp_path)
    memory, scope, veto = state

    def mutation(self):
        if target == "item_revision":
            object.__setattr__(self.items[0], "revision", 999)
        elif target == "item_state":
            object.__setattr__(self.items[0], "state", RetentionState.EXPIRED)
        elif target == "owner":
            object.__setattr__(scope, "owner_id", "different-owner")
        elif target == "memory_path":
            memory.path = Path(str(tmp_path / "other-memory.sqlite"))
        else:
            veto.path = Path(str(tmp_path / "other-veto.sqlite"))
        return False

    monkeypatch.setattr(
        SyntheticRetentionInventory, "context_use_authorized",
        property(mutation),
    )
    with pytest.raises(SyntheticRetentionRejected, match="changed"):
        invoke(state)
