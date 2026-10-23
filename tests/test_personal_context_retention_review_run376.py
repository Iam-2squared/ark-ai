"""Retention inventory is an inert privacy diagnostic, never erasure proof."""

import sqlite3
from pathlib import Path

import pytest

from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_retention_review import (
    RetentionState,
    SyntheticRetentionRejected,
    review_synthetic_retention_inventory,
)
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


def _setup(path: Path):
    memory = SQLiteMemoryStore(path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("owner", "profile")
    for source, expiry in (
        ("expired", 99), ("boundary", 100),
        ("future", 101), ("unbounded", None),
    ):
        memory.put(MemoryWrite(
            scope, source, "private-test-fixture-" + source,
            expires_at_ms=expiry,
        ))
    memory.put(MemoryWrite(
        MemoryScope("other-owner", "profile"), "other", "not-our-row",
    ))
    veto = SyntheticContextRevocationLedger(path / "veto.sqlite")
    return memory, scope, veto


def _review(state, **changes):
    memory, scope, veto = state
    values = {"now_ms": 100}
    values.update(changes)
    return review_synthetic_retention_inventory(memory, scope, veto, **values)


def test_expiry_boundary_unbounded_review_and_no_erasure_authority(tmp_path: Path):
    result = _review(_setup(tmp_path))
    assert len(result.items) == 4
    assert result.expired_count == 2
    assert {item.state for item in result.items} == {
        RetentionState.EXPIRED, RetentionState.NOT_EXPIRED, RetentionState.NO_EXPIRY,
    }
    assert all(item.memory_id.startswith("mem_") for item in result.items)
    assert all(item.revision == 1 for item in result.items)
    assert result.erasure_completed is False
    assert result.deletion_authorized is False
    assert result.context_use_authorized is False
    assert "private-test-fixture" not in repr(result)
    assert "not-our-row" not in repr(result)


def test_repeat_is_stable_and_time_change_reclassifies(tmp_path: Path):
    state = _setup(tmp_path)
    first = _review(state)
    assert first == _review(state)
    later = _review(state, now_ms=101)
    assert later.expired_count == 3
    assert later.inventory_digest != first.inventory_digest


def test_scope_veto_is_diagnostic_not_erasure_or_consented_use(tmp_path: Path):
    state = _setup(tmp_path)
    state[2].revoke(state[1], at_ms=100)
    result = _review(state)
    assert result.revoked is True
    assert result.context_use_authorized is False
    assert result.erasure_completed is False


def test_unrelated_veto_is_not_scope_veto(tmp_path: Path):
    state = _setup(tmp_path)
    state[2].revoke(MemoryScope("owner", "other"), at_ms=100)
    assert _review(state).revoked is False


def test_independently_retained_veto_detects_deletion(tmp_path: Path):
    state = _setup(tmp_path)
    state[2].revoke(MemoryScope("owner", "other"), at_ms=100)
    witness = review_revocation_continuity(state[2])
    with sqlite3.connect(state[2].path) as conn:
        conn.execute("DELETE FROM synthetic_context_revocations")
    with pytest.raises(SyntheticContextRevocationRejected, match="history changed"):
        _review(state, retained_revocations=witness)


@pytest.mark.parametrize("now", [-1, True, "100", 2**63])
def test_invalid_exact_now_rejected(tmp_path: Path, now):
    state = _setup(tmp_path)
    with pytest.raises(SyntheticRetentionRejected, match="exact bounded"):
        _review(state, now_ms=now)


@pytest.mark.parametrize("limit", [-1, 0, True, 1001, "1000"])
def test_invalid_record_budget_rejected(tmp_path: Path, limit):
    state = _setup(tmp_path)
    with pytest.raises(SyntheticRetentionRejected, match="exact bounded"):
        _review(state, max_records=limit)


def test_valid_small_budget_fails_closed_without_partial_result(tmp_path: Path):
    state = _setup(tmp_path)
    with pytest.raises(SyntheticRetentionRejected, match="budget exceeded"):
        _review(state, max_records=2)


def test_clock_older_than_persisted_memory_is_refused(tmp_path: Path):
    state = _setup(tmp_path)
    with pytest.raises(SyntheticRetentionRejected, match="caller clock"):
        _review(state, now_ms=99)


def test_stored_content_tamper_is_rejected_not_exposed(tmp_path: Path):
    state = _setup(tmp_path)
    with sqlite3.connect(state[0].path) as conn:
        conn.execute(
            "UPDATE memories SET content='tampered' WHERE source_id='future'"
        )
    with pytest.raises(ValueError, match="digest"):
        _review(state)


def test_missing_memory_file_does_not_create_blank_database(tmp_path: Path):
    state = _setup(tmp_path)
    missing = tmp_path / "memory-gone.sqlite"
    state[0].path.rename(missing)
    with pytest.raises(sqlite3.OperationalError):
        _review(state)
    assert not state[0].path.exists()


def test_invalid_ledger_or_scope_type_denied(tmp_path: Path):
    state = _setup(tmp_path)
    with pytest.raises(SyntheticRetentionRejected, match="exact bounded"):
        review_synthetic_retention_inventory(state[0], "owner", state[2], now_ms=100)
    with pytest.raises(SyntheticRetentionRejected, match="exact bounded"):
        review_synthetic_retention_inventory(state[0], state[1], None, now_ms=100)
