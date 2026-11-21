"""Synthetic history readers never create replacement SQLite databases."""

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.audit_continuity_review import review_audit_continuity
from ark.agency.contracts import ActionAuditSchemaError, ToolCall
from ark.memory.coherent_snapshot_review import (
    CoherentSnapshotRequest,
    review_coherent_snapshot,
)
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def test_memory_snapshot_missing_database_fails_without_file_creation(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "existing.db", clock_ms=lambda: 100)
    missing = tmp_path / "not-created.db"
    store.path = missing
    with pytest.raises(MemorySchemaError, match="read-only"):
        review_coherent_snapshot(store, CoherentSnapshotRequest("fixture", ("test",)))
    assert not missing.exists()


def test_audit_review_missing_database_fails_without_file_creation(tmp_path):
    audit = SQLiteActionAudit(tmp_path / "existing.db", clock_ms=lambda: 100)
    missing = tmp_path / "not-created.db"
    audit.path = missing
    with pytest.raises(ActionAuditSchemaError, match="cannot read audit snapshot"):
        review_audit_continuity(audit)
    assert not missing.exists()


def test_readonly_memory_snapshot_handles_percent_encoded_path(tmp_path):
    scope = MemoryScope("fixture-owner", "fixture-space")
    store = SQLiteMemoryStore(
        tmp_path / "space # directory" / "memory # sample.db", clock_ms=lambda: 100
    )
    created = store.put(MemoryWrite(scope, "source", "synthetic-only"))
    review = review_coherent_snapshot(
        store, CoherentSnapshotRequest(scope.owner_id, (scope.namespace,))
    )
    assert review.records[0][0].memory_id == created.memory_id


def test_readonly_audit_review_handles_percent_encoded_path(tmp_path):
    audit = SQLiteActionAudit(
        tmp_path / "space # directory" / "audit # sample.db", clock_ms=lambda: 100
    )
    audit.append(
        ToolCall("fixture.tool", "fixture.cap", "scope:synthetic"),
        outcome="synthetic-only",
    )
    review = review_audit_continuity(audit)
    assert review.event_count == 1
    assert review.tail_event_id == 1
