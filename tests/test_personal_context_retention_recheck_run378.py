"""Previously captured retention data must be rechecked before dry-run review."""

import sqlite3
from pathlib import Path

import pytest

from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_retention_recheck_review import (
    SyntheticRetentionRecheckRejected,
    review_synthetic_retention_recheck,
)
from ark.personal_context_retention_review import review_synthetic_retention_inventory
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


def _fixture(tmp_path: Path):
    memory = SQLiteMemoryStore(tmp_path / "memory #1 %.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("test-owner", "profile")
    for source, expires in (("expired", 99), ("future", 101), ("no-expiry", None)):
        memory.put(MemoryWrite(
            scope, source, "PRIVATE-CONTEXT-" + source, expires_at_ms=expires,
        ))
    memory.put(MemoryWrite(
        MemoryScope("someone-else", "profile"), "outside", "unrelated-private",
    ))
    veto = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    cached = review_synthetic_retention_inventory(memory, scope, veto, now_ms=100)
    return memory, scope, veto, cached


def _review(state, **changes):
    memory, scope, veto, cached = state
    values = {"now_ms": 101, "max_age_ms": 5}
    values.update(changes)
    return review_synthetic_retention_recheck(
        memory, scope, veto, cached, **values,
    )


def test_new_expiry_boundary_is_reclassified_but_never_authorizes(tmp_path: Path):
    state = _fixture(tmp_path)
    result = _review(state)
    assert len(result.expired_memory_ids) == 2
    assert len(result.unbounded_memory_ids) == 1
    assert result.current_inventory_digest != result.captured_inventory_digest
    assert result.scope_digest == state[3].scope_digest
    assert result.deletion_authorized is False
    assert result.erasure_completed is False
    assert result.context_use_authorized is False
    assert result.external_disclosure_authorized is False
    assert "PRIVATE-CONTEXT" not in repr(result)
    assert "unrelated-private" not in repr(result)


def test_same_moment_retention_review_is_stable(tmp_path: Path):
    state = _fixture(tmp_path)
    result = _review(state, now_ms=100)
    assert result.current_inventory_digest == state[3].inventory_digest
    assert len(result.expired_memory_ids) == 1


@pytest.mark.parametrize(("now", "age"), [(99, 10), (106, 5), (101, 0), (True, 5), (101, True), (2**63, 5)])
def test_expired_regressed_and_nonexact_clock_inputs(tmp_path: Path, now, age):
    with pytest.raises(SyntheticRetentionRecheckRejected, match="exact|expired"):
        _review(_fixture(tmp_path), now_ms=now, max_age_ms=age)


def test_added_memory_after_capture_invalidates_inventory(tmp_path: Path):
    state = _fixture(tmp_path)
    state[0].put(MemoryWrite(state[1], "new", "new-private", expires_at_ms=101))
    with pytest.raises(SyntheticRetentionRecheckRejected, match="changed"):
        _review(state)


def test_existing_row_content_revision_change_is_denied(tmp_path: Path):
    state = _fixture(tmp_path)
    state[0].put(MemoryWrite(state[1], "future", "changed-private", expires_at_ms=101))
    with pytest.raises(SyntheticRetentionRecheckRejected, match="changed"):
        _review(state)


def test_forged_stored_content_is_not_returned(tmp_path: Path):
    state = _fixture(tmp_path)
    with sqlite3.connect(state[0].path) as conn:
        conn.execute("UPDATE memories SET content='tampered' WHERE source_id='future'")
    with pytest.raises(MemorySchemaError, match="digest"):
        _review(state)


def test_new_revocation_is_a_veto_even_without_memory_change(tmp_path: Path):
    state = _fixture(tmp_path)
    state[2].revoke(state[1], at_ms=101)
    with pytest.raises(SyntheticRetentionRecheckRejected, match="changed"):
        _review(state)


def test_unrelated_revocation_update_is_also_fenced(tmp_path: Path):
    state = _fixture(tmp_path)
    state[2].revoke(MemoryScope("other", "other"), at_ms=101)
    with pytest.raises(SyntheticRetentionRecheckRejected, match="changed"):
        _review(state)


def test_older_independent_revocation_witness_detects_deletion(tmp_path: Path):
    state = _fixture(tmp_path)
    state[2].revoke(MemoryScope("older", "scope"), at_ms=100)
    witness = review_revocation_continuity(state[2])
    with sqlite3.connect(state[2].path) as conn:
        conn.execute("DELETE FROM synthetic_context_revocations")
    with pytest.raises(SyntheticContextRevocationRejected, match="history changed"):
        _review(state, retained_revocations=witness)


def test_new_memory_created_during_recheck_fails_closed(tmp_path: Path, monkeypatch):
    import ark.personal_context_retention_recheck_review as module

    state = _fixture(tmp_path)
    original = module.review_synthetic_retention_inventory
    count = 0

    def injected(*args, **kwargs):
        nonlocal count
        observed = original(*args, **kwargs)
        count += 1
        if count == 1:
            state[0].put(MemoryWrite(
                state[1], "late", "late-private", expires_at_ms=102,
            ))
        return observed

    monkeypatch.setattr(module, "review_synthetic_retention_inventory", injected)
    with pytest.raises(SyntheticRetentionRecheckRejected, match="drifted"):
        _review(state)


def test_reflectively_edited_cached_inventory_is_rejected(tmp_path: Path):
    state = _fixture(tmp_path)
    object.__setattr__(state[3], "inventory_digest", "retention_" + "0" * 64)
    with pytest.raises(SyntheticRetentionRecheckRejected, match="changed"):
        _review(state)


def test_missing_memory_file_is_not_recreated(tmp_path: Path):
    state = _fixture(tmp_path)
    original = state[0].path
    original.rename(tmp_path / "moved.sqlite")
    with pytest.raises(sqlite3.OperationalError):
        _review(state)
    assert not original.exists()


def test_wrong_inventory_and_scope_types_fail_closed(tmp_path: Path):
    state = _fixture(tmp_path)
    with pytest.raises(SyntheticRetentionRecheckRejected, match="exact"):
        review_synthetic_retention_recheck(
            state[0], state[1], state[2], object(), now_ms=101, max_age_ms=5,
        )
    with pytest.raises(SyntheticRetentionRecheckRejected, match="exact"):
        review_synthetic_retention_recheck(
            state[0], "scope", state[2], state[3], now_ms=101, max_age_ms=5,
        )
