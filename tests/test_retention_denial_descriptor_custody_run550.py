"""A synthetic retention report cannot swap a denial getter for False."""

from __future__ import annotations

import pytest

import ark.personal_context_retention_review as mod
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def fixture(tmp_path):
    memory = SQLiteMemoryStore(
        tmp_path / "private-memory.sqlite", clock_ms=lambda: 100,
    )
    scope = MemoryScope("offline-owner", "offline-profile")
    memory.put(MemoryWrite(scope, "fixture", "SENSITIVE-TEST-CONTENT"))
    ledger = SyntheticContextRevocationLedger(tmp_path / "private-veto.sqlite")
    return memory, scope, ledger


@pytest.mark.parametrize(
    "name",
    ("erasure_completed", "deletion_authorized", "context_use_authorized"),
)
def test_false_only_descriptor_replacement_prior_to_review_is_denied(
    tmp_path, monkeypatch, name,
):
    args = fixture(tmp_path)
    monkeypatch.setattr(
        mod.SyntheticRetentionInventory, name,
        property(lambda self: False),
    )
    with pytest.raises(mod.SyntheticRetentionRejected, match="descriptor changed"):
        mod.review_synthetic_retention_inventory(*args, now_ms=100)


@pytest.mark.parametrize(
    "name",
    ("erasure_completed", "deletion_authorized"),
)
def test_false_getter_can_swap_other_false_descriptor_but_never_return(
    tmp_path, monkeypatch, name,
):
    args = fixture(tmp_path)
    original = getattr(mod.SyntheticRetentionInventory, name)

    def swap(self):
        monkeypatch.setattr(
            mod.SyntheticRetentionInventory, "context_use_authorized",
            property(lambda current: False),
        )
        return False

    monkeypatch.setattr(
        mod.SyntheticRetentionInventory, name,
        property(swap),
    )
    with pytest.raises(mod.SyntheticRetentionRejected, match="descriptor changed"):
        mod.review_synthetic_retention_inventory(*args, now_ms=100)
    assert original is not getattr(mod.SyntheticRetentionInventory, name)


def test_normal_inventory_remains_inert_and_minimized(tmp_path):
    args = fixture(tmp_path)
    report = mod.review_synthetic_retention_inventory(*args, now_ms=100)
    assert report.erasure_completed is False
    assert report.deletion_authorized is False
    assert report.context_use_authorized is False
    assert len(report.items) == 1
    assert "SENSITIVE-TEST-CONTENT" not in repr(report)
