"""Ephemeral context must not mix identity or provenance epochs across hashing."""

import hashlib
from types import MappingProxyType

import pytest

import ark.personal_context_review as module
from ark.memory.coherent_snapshot_review import CoherentSnapshotReview
from ark.memory.contracts import MemoryRecord, MemoryScope
from ark.memory.sqlite_store import deterministic_memory_id
from ark.personal_context_review import (
    ContextSelectionPolicy,
    PersonalContextReviewRejected,
)


def _fixture():
    scope = MemoryScope("offline-owner", "notes")
    # Distinct, value-equal scope carrier checks both the snapshot scope and
    # each record's own provenance, not merely their reference identities.
    record_scope = MemoryScope("offline-owner", "notes")
    record = MemoryRecord(
        deterministic_memory_id(scope, "synthetic-source"), record_scope,
        "synthetic-source", "PRIVATE OFFLINE FIXTURE", {"purpose": "local"},
        10, 20, 200, 1,
        hashlib.sha256(b"PRIVATE OFFLINE FIXTURE").hexdigest(),
    )
    snapshot = CoherentSnapshotReview(100, (scope,), ((record,),), "f" * 64)
    return snapshot, record


def test_stable_ephemeral_projection_remains_non_authoritative():
    snapshot, _record = _fixture()
    result = module.review_personal_context(snapshot, ContextSelectionPolicy(1, 1))
    assert result.snapshot_digest == "f" * 64
    assert result.action_authorized is False
    assert result.dispatch_authorized is False
    assert "PRIVATE OFFLINE FIXTURE" not in result.bundle_id


@pytest.mark.parametrize("change", [
    "snapshot_digest", "snapshot_clock", "scope_owner",
    "record_source", "record_expiry", "record_metadata", "record_scope_owner",
])
def test_reflected_mutation_after_provenance_hash_is_rejected(monkeypatch, change: str):
    snapshot, record = _fixture()
    original = module._hash

    def inject(label, payload):
        digest = original(label, payload)
        if label == "ARK-context-provenance-v1":
            if change == "snapshot_digest":
                object.__setattr__(snapshot, "provenance_sha256", "e" * 64)
            elif change == "snapshot_clock":
                object.__setattr__(snapshot, "read_at_ms", 105)
            elif change == "scope_owner":
                object.__setattr__(snapshot.scopes[0], "owner_id", "different-owner")
            elif change == "record_source":
                object.__setattr__(record, "source_id", "different-source")
            elif change == "record_expiry":
                object.__setattr__(record, "expires_at_ms", 50)
            elif change == "record_metadata":
                object.__setattr__(
                    record, "metadata", MappingProxyType({"purpose": "changed"}),
                )
            else:
                object.__setattr__(record.scope, "owner_id", "different-owner")
        return digest

    monkeypatch.setattr(module, "_hash", inject)
    with pytest.raises(PersonalContextReviewRejected, match="context input changed"):
        module.review_personal_context(snapshot, ContextSelectionPolicy(1, 1))


def test_snapshot_header_mutation_during_final_bundle_hash_is_rejected(monkeypatch):
    snapshot, _record = _fixture()
    original = module._hash

    def inject(label, payload):
        digest = original(label, payload)
        if label == "ARK-context-bundle-v1":
            object.__setattr__(snapshot, "provenance_sha256", "e" * 64)
        return digest

    monkeypatch.setattr(module, "_hash", inject)
    with pytest.raises(PersonalContextReviewRejected, match="context input changed"):
        module.review_personal_context(snapshot, ContextSelectionPolicy(1, 1))
