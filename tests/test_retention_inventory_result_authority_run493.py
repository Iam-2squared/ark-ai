"""A retention inventory is diagnostic even when class properties are patched.

All Memory data is local and synthetic. No purge, export or disclosure occurs.
"""

from __future__ import annotations

import pytest

import ark.personal_context_retention_review as retention
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def _review(tmp_path):
    memory = SQLiteMemoryStore(
        tmp_path / "memory.sqlite", clock_ms=lambda: 100,
    )
    scope = MemoryScope("local-owner", "profile")
    memory.put(MemoryWrite(
        scope, "synthetic", "PRIVATE-LOCAL-FIXTURE",
        expires_at_ms=110,
    ))
    veto = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    return retention.review_synthetic_retention_inventory(
        memory, scope, veto, now_ms=100,
    )


@pytest.mark.parametrize(
    "name",
    ("erasure_completed", "deletion_authorized", "context_use_authorized"),
)
def test_inventory_reflective_authority_spoof_is_denied(tmp_path, monkeypatch, name):
    monkeypatch.setattr(
        retention.SyntheticRetentionInventory,
        name,
        property(lambda self: True),
    )
    with pytest.raises(retention.SyntheticRetentionRejected, match="result changed"):
        _review(tmp_path)


def test_unmodified_inventory_is_content_free_and_non_authorizing(tmp_path):
    result = _review(tmp_path)
    assert result.erasure_completed is False
    assert result.deletion_authorized is False
    assert result.context_use_authorized is False
    assert len(result.items) == 1
    assert "PRIVATE-LOCAL-FIXTURE" not in repr(result)
