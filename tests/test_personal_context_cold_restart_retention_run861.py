"""Cold-restart Personal Context retention review with detached private inputs.

Synthetic SQLite only. Inventory and revocation observations are not erasure,
consent, external disclosure or a trusted clock. No live context is exported.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_retention_recheck_review import (
    SyntheticRetentionRecheckRejected,
    review_synthetic_retention_recheck,
)
from ark.personal_context_retention_review import review_synthetic_retention_inventory
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def _snapshot(root: Path):
    memory_path = root / "retention.sqlite"
    revocation_path = root / "revocation.sqlite"
    scope = MemoryScope("private-owner", "profile")
    memory = SQLiteMemoryStore(memory_path, clock_ms=lambda: 100)
    saved = memory.put(
        MemoryWrite(
            scope, "source", "SENSITIVE-CONTEXT-NOT-FOR-OUTPUT",
            expires_at_ms=150,
        )
    )
    veto = SyntheticContextRevocationLedger(revocation_path)
    cached = review_synthetic_retention_inventory(memory, scope, veto, now_ms=100)
    return memory_path, revocation_path, scope, saved, cached


def _cold(root: Path):
    return (
        SQLiteMemoryStore(root / "retention.sqlite", clock_ms=lambda: 151),
        SyntheticContextRevocationLedger(root / "revocation.sqlite"),
    )


def _check(memory, scope, veto, cached):
    return review_synthetic_retention_recheck(
        memory, scope, veto, cached, now_ms=151, max_age_ms=60,
    )


def test_cold_restart_reclassifies_expiry_without_disclosing_private_data(
    tmp_path: Path,
) -> None:
    _memory_path, _veto_path, scope, saved, cached = _snapshot(tmp_path)
    memory, veto = _cold(tmp_path)
    result = _check(memory, scope, veto, cached)
    assert result.expired_memory_ids == (saved.memory_id,)
    assert result.unbounded_memory_ids == ()
    assert result.deletion_authorized is False
    assert result.erasure_completed is False
    assert result.context_use_authorized is False
    assert result.external_disclosure_authorized is False
    assert "SENSITIVE-CONTEXT-NOT-FOR-OUTPUT" not in repr(result)


def test_cold_restart_detects_new_revocation_and_never_reuses_cached_context(
    tmp_path: Path,
) -> None:
    _memory_path, _veto_path, scope, _saved, cached = _snapshot(tmp_path)
    memory, veto = _cold(tmp_path)
    veto.revoke(scope, at_ms=150)
    with pytest.raises(SyntheticRetentionRecheckRejected) as failure:
        _check(memory, scope, veto, cached)
    assert "SENSITIVE-CONTEXT-NOT-FOR-OUTPUT" not in str(failure.value)
    assert "private-owner" not in str(failure.value)


def test_cold_restart_detects_independent_memory_update_without_private_echo(
    tmp_path: Path,
) -> None:
    _memory_path, _veto_path, scope, _saved, cached = _snapshot(tmp_path)
    memory, veto = _cold(tmp_path)
    memory.put(
        MemoryWrite(
            scope, "source", "SENSITIVE-UPDATED-NEVER-ECHO",
            expires_at_ms=150,
        ),
        expected_revision=1,
    )
    with pytest.raises(SyntheticRetentionRecheckRejected) as failure:
        _check(memory, scope, veto, cached)
    assert "SENSITIVE-UPDATED-NEVER-ECHO" not in str(failure.value)
    assert "private-owner" not in str(failure.value)
