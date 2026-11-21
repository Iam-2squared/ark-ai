"""Private Memory alignment scans fail closed on substituted digest callbacks.

Synthetic SQLite only; no real memory disclosure, consent or backend action.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import sqlite_event_alignment as alignment


def _store(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: 5000)
    store.put(MemoryWrite(
        MemoryScope("owner"), "fixture", "private local fixture",
        metadata={"secret": "not for unreviewed callbacks"},
    ))
    return store


@pytest.mark.parametrize("dependency", ("sha256", "dumps"))
def test_substituted_digest_dependency_denied_before_sqlite(
    tmp_path, monkeypatch, dependency,
):
    store = _store(tmp_path)
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        pytest.fail("unreviewed digest/JSON callback must not run")

    monkeypatch.setattr(getattr(alignment, "hashlib" if dependency == "sha256"
                                else "json"), dependency, forbidden)

    def forbidden_read():
        pytest.fail("rejected audit must not open private SQLite")

    monkeypatch.setattr(store, "_connect_readonly", forbidden_read)
    with pytest.raises(alignment.MemoryEventAlignmentRejected, match="digest authority"):
        alignment.review_memory_event_alignment(store)
    assert calls == []


def test_reentrant_row_decode_cannot_redirect_metadata_digest(
    tmp_path, monkeypatch,
):
    store = _store(tmp_path)
    original_record = alignment._record
    seen = []

    def rogue(*_args, **_kwargs):
        seen.append("called")
        pytest.fail("unreviewed SHA-256 must not receive metadata")

    def replaced_record(row):
        record = original_record(row)
        monkeypatch.setattr(alignment.hashlib, "sha256", rogue)
        return record

    monkeypatch.setattr(alignment, "_record", replaced_record)
    with pytest.raises(alignment.MemoryEventAlignmentRejected, match="digest authority"):
        alignment.review_memory_event_alignment(store)
    assert seen == []


def test_reentrant_charge_cannot_redirect_event_json(
    tmp_path, monkeypatch,
):
    store = _store(tmp_path)
    original_charge = alignment._charge
    seen = []

    def rogue(*_args, **_kwargs):
        seen.append("called")
        pytest.fail("unreviewed JSON encoder must not receive audit fields")

    def replaced_charge(digest, entry):
        if entry[0] == "event":
            monkeypatch.setattr(alignment.json, "dumps", rogue)
        return original_charge(digest, entry)

    monkeypatch.setattr(alignment, "_charge", replaced_charge)
    with pytest.raises(alignment.MemoryEventAlignmentRejected, match="digest authority"):
        alignment.review_memory_event_alignment(store)
    assert seen == []
