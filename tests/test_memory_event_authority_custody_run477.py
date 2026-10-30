"""Memory event witnesses cannot acquire privileges during history replay."""

from __future__ import annotations

import pytest

import ark.memory.synthetic_event_continuity_review as mod
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _store(tmp_path, *, updates=0):
    memory = SQLiteMemoryStore(tmp_path / "events.sqlite3", clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "private")
    memory.put(MemoryWrite(scope, "source", "synthetic-first"))
    for index in range(updates):
        memory.put(
            MemoryWrite(scope, "source", f"synthetic-update-{index}"),
            expected_revision=index + 1,
        )
    return memory, scope


@pytest.mark.parametrize("field", (
    "deletion_authorized",
    "context_use_authorized",
    "external_disclosure_authorized",
))
def test_refuses_retained_witness_claiming_privilege(
    tmp_path, monkeypatch, field,
):
    memory, scope = _store(tmp_path)
    retained = mod.review_synthetic_memory_event_continuity(memory, scope)
    monkeypatch.setattr(
        mod.SyntheticMemoryEventWitness,
        field, property(lambda _witness: True),
    )
    with pytest.raises(mod.SyntheticMemoryEventRejected, match="retained"):
        mod.review_synthetic_memory_event_continuity(
            memory, scope, retained=retained,
        )
    assert len(memory.events(scope)) == 1


@pytest.mark.parametrize("field", (
    "deletion_authorized",
    "context_use_authorized",
    "external_disclosure_authorized",
))
def test_rejects_earlier_prefix_claiming_authority_mid_replay(
    tmp_path, monkeypatch, field,
):
    memory, scope = _store(tmp_path, updates=1)
    original_hash = mod._hash
    count = 0

    def malicious_hash(label, values):
        nonlocal count
        if label == "ARK-synthetic-memory-event-v1":
            count += 1
            if count == 2:
                # Prefix 1 was constructed and accepted before this callback.
                # Only that old prefix becomes privileged; prefix 2 remains inert.
                monkeypatch.setattr(
                    mod.SyntheticMemoryEventWitness,
                    field, property(lambda receipt: receipt.event_count == 1),
                )
        return original_hash(label, values)

    monkeypatch.setattr(mod, "_hash", malicious_hash)
    with pytest.raises(mod.SyntheticMemoryEventRejected, match="earlier"):
        mod.review_synthetic_memory_event_continuity(memory, scope)
    assert len(memory.events(scope)) == 2


def test_non_authorizing_retained_prefix_can_prove_local_continuity(tmp_path):
    memory, scope = _store(tmp_path)
    retained = mod.review_synthetic_memory_event_continuity(memory, scope)
    memory.put(
        MemoryWrite(scope, "source", "synthetic-second"),
        expected_revision=1,
    )
    result = mod.review_synthetic_memory_event_continuity(
        memory, scope, retained=retained,
    )
    assert result.event_count == 2
    assert result.deletion_authorized is False
    assert result.context_use_authorized is False
    assert result.external_disclosure_authorized is False
    assert "synthetic-second" not in repr(result)
