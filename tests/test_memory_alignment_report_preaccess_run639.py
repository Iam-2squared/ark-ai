"""Inert event-alignment review must reject altered result hooks before SQLite.

No test replaces __new__ on an existing Python class: doing so can mutate
CPython's tp_new slot beyond pytest's normal monkeypatch teardown.
"""

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import sqlite_event_alignment as audit


@pytest.mark.parametrize(
    "mutation",
    [
        "exported",
        "initializer",
        "row_count",
        "digest",
        "getattribute",
        "getattr",
        "authority",
    ],
)
def test_alignment_rejects_result_contract_change_before_private_read(
    tmp_path, monkeypatch, mutation,
):
    store = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: 5000)
    store.put(MemoryWrite(MemoryScope("owner"), "source", "secret"))
    review_type = audit.MemoryEventAlignmentReview

    def rogue(*_args, **_kwargs):
        pytest.fail("injected result hook must never execute")

    if mutation == "exported":
        monkeypatch.setattr(audit, "MemoryEventAlignmentReview", object)
    elif mutation == "initializer":
        monkeypatch.setattr(review_type, "__init__", rogue)
    elif mutation in {"row_count", "digest"}:
        monkeypatch.setattr(review_type, mutation, property(rogue))
    elif mutation == "getattribute":
        monkeypatch.setattr(review_type, "__getattribute__", rogue, raising=False)
    elif mutation == "getattr":
        monkeypatch.setattr(review_type, "__getattr__", rogue, raising=False)
    else:
        monkeypatch.setattr(review_type, "action_authorized", property(rogue))

    def forbidden_read():
        pytest.fail("denied alignment review opened private SQLite")

    monkeypatch.setattr(store, "_connect_readonly", forbidden_read)
    with pytest.raises(audit.MemoryEventAlignmentRejected, match="authority epoch"):
        audit.review_memory_event_alignment(store)


def test_unmodified_alignment_remains_repeatable_and_deny_only(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "memory.db", clock_ms=lambda: 5000)
    record = store.put(MemoryWrite(MemoryScope("owner"), "source", "secret"))
    first = audit.review_memory_event_alignment(store)
    second = audit.review_memory_event_alignment(store)
    assert first == second
    assert (first.row_count, first.event_count, first.last_event_id) == (1, 1, 1)
    assert first.digest == second.digest
    assert record.memory_id not in repr(first)
    assert first.independently_authenticated is False
    assert first.user_consent_verified is False
    assert first.deletion_or_erasure_proven is False
    assert first.action_authorized is False
