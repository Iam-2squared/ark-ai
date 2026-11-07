"""Dual CAS uncertainty and independent scoped privacy veto never grant reuse.

An independent local writer may write the proposed bytes, unrelated bytes or
an unrelated row. Two read-only reviewers cannot attribute that commit to
the caller; an independently persisted scope veto cannot be cleared by it.
No real personal information, tool, network or external WRITE is used.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.ambiguous_commit_pair_review import review_memory_ambiguous_commit_pair
from ark.memory.generation_fenced_cas import (
    generation_fenced_memory_update,
    observe_memory_generation_for_cas,
)
from ark.personal_context_retention_review import review_synthetic_retention_inventory
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


@pytest.mark.parametrize(
    ("intervention", "disposition"),
    (
        ("no_write", "LOCAL_UNCHANGED_REVIEW"),
        ("same_bytes", "MATCHING_ROW_MANUAL_REVIEW"),
        ("different_bytes", "DIVERGED_MANUAL_REVIEW"),
        ("unrelated_owner_write", "LOCAL_UNCHANGED_REVIEW"),
    ),
)
def test_ambiguous_cas_review_cannot_override_independent_privacy_veto(
    tmp_path, intervention, disposition,
):
    path = tmp_path / "memory.sqlite"
    scope = MemoryScope("private-owner", "retained")
    reader = SQLiteMemoryStore(path, clock_ms=lambda: 100)
    writer = SQLiteMemoryStore(path, clock_ms=lambda: 110)
    created = reader.put(
        MemoryWrite(scope, "source", "fixture-before", expires_at_ms=500),
    )
    retained = observe_memory_generation_for_cas(reader, scope, "source")
    proposed = MemoryWrite(
        scope, "source", "fixture-after",
        metadata={"synthetic": "true"}, expires_at_ms=400,
    )
    if intervention == "same_bytes":
        generation_fenced_memory_update(writer, proposed, retained=retained)
    elif intervention == "different_bytes":
        generation_fenced_memory_update(
            writer,
            MemoryWrite(
                scope, "source", "different-fixture",
                metadata={"synthetic": "false"}, expires_at_ms=400,
            ),
            retained=retained,
        )
    elif intervention == "unrelated_owner_write":
        writer.put(MemoryWrite(
            MemoryScope("another-owner", "retained"),
            "source", "unrelated-fixture", expires_at_ms=400,
        ))

    veto_path = tmp_path / "veto.sqlite"
    veto = SyntheticContextRevocationLedger(veto_path)
    veto.revoke(scope, at_ms=120)
    prior_events = tuple(reader.events(scope))
    prior_record = reader.get(created.memory_id, scope, include_expired=True)

    report = review_memory_ambiguous_commit_pair(
        SQLiteMemoryStore(path, clock_ms=lambda: 130),
        proposed, retained=retained,
    )
    assert report.disposition == disposition
    for name in (
        "caller_commit_authenticated", "automatic_retry_authorized",
        "write_authorized", "trusted_clock_verified",
    ):
        assert getattr(report, name) is False

    for memory_store, ledger in (
        (reader, veto),
        (
            SQLiteMemoryStore(path, clock_ms=lambda: 130),
            SyntheticContextRevocationLedger(veto_path),
        ),
    ):
        inventory = review_synthetic_retention_inventory(
            memory_store, scope, ledger, now_ms=130,
        )
        assert inventory.revoked is True
        assert inventory.context_use_authorized is False
        assert inventory.deletion_authorized is False
        assert inventory.erasure_completed is False
        assert len(inventory.items) == 1
        assert inventory.items[0].memory_id == created.memory_id
        assert inventory.items[0].revision == (
            2 if intervention in ("same_bytes", "different_bytes") else 1
        )
        for private_payload in (
            "fixture-before", "fixture-after", "different-fixture",
            "unrelated-fixture",
        ):
            assert private_payload not in repr(inventory)
            assert private_payload not in repr(report)

    assert tuple(reader.events(scope)) == prior_events
    assert reader.get(created.memory_id, scope, include_expired=True) == prior_record
    assert retained.external_action_authorized is False
    assert retained.consent_authenticated is False
