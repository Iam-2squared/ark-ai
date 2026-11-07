"""Read-only retained synthetic witnesses detect locally rewritten history."""

import hashlib
import sqlite3
from pathlib import Path

import pytest

from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)
from ark.agency.registry import ToolRegistration, ToolRegistry
from ark.agency.synthetic_occurrence_continuity_review import (
    assert_synthetic_history_continues,
    read_synthetic_ledger_witness,
)


class NeverExecuted:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("offline fixture cannot execute a tool")


def _reserve(store: SyntheticOccurrenceStore, name: str):
    registry = ToolRegistry(
        (ToolRegistration("mock", "fixture", Effect.WRITE, "offline", NeverExecuted()),)
    )
    call = ToolCall("mock", "fixture", "test", {"n": 1})
    store.reserve_synthetic(
        registry, call, OneShotAuthorization("synthetic-" + name, call.request_id, 1000),
        occurrence_id="occ_" + hashlib.sha256(name.encode()).hexdigest(),
        now_ms=20,
    )


def test_retained_witness_survives_append_and_reopen(tmp_path: Path):
    path = tmp_path / "fixture.sqlite"
    store = SyntheticOccurrenceStore(path)
    empty = read_synthetic_ledger_witness(path)
    _reserve(store, "A")
    first = read_synthetic_ledger_witness(path)
    _reserve(SyntheticOccurrenceStore(path), "B")
    second = read_synthetic_ledger_witness(path)
    assert len(empty.row_hashes) == 0
    assert len(first.row_hashes) == 1
    assert len(second.row_hashes) == 2
    assert first.digest != second.digest
    assert_synthetic_history_continues(empty, first)
    assert_synthetic_history_continues(first, second)
    assert_synthetic_history_continues(second, second)
    with pytest.raises(SyntheticReplayRejected, match="history changed"):
        assert_synthetic_history_continues(second, first)


def test_same_schema_tail_deletion_rejected_only_with_retained_witness(tmp_path: Path):
    path = tmp_path / "fixture.sqlite"
    store = SyntheticOccurrenceStore(path)
    _reserve(store, "A")
    kept = read_synthetic_ledger_witness(path)
    with sqlite3.connect(path) as conn:
        conn.execute("DELETE FROM synthetic_occurrence_reservations")
    current = read_synthetic_ledger_witness(path)
    assert len(current.row_hashes) == 0
    with pytest.raises(SyntheticReplayRejected, match="history changed"):
        assert_synthetic_history_continues(kept, current)


def test_same_schema_canonical_row_rewrite_fails_retained_comparison(tmp_path: Path):
    path = tmp_path / "fixture.sqlite"
    store = SyntheticOccurrenceStore(path)
    _reserve(store, "A")
    kept = read_synthetic_ledger_witness(path)
    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE synthetic_occurrence_reservations SET request_id=?",
            ("act_" + "f" * 64,),
        )
    current = read_synthetic_ledger_witness(path)
    assert len(current.row_hashes) == 1
    with pytest.raises(SyntheticReplayRejected, match="history changed"):
        assert_synthetic_history_continues(kept, current)


def test_reflective_witness_digest_mutation_is_rejected(tmp_path: Path):
    path = tmp_path / "fixture.sqlite"
    SyntheticOccurrenceStore(path)
    kept = read_synthetic_ledger_witness(path)
    object.__setattr__(kept, "digest", "synthetic_ledger_" + "0" * 64)
    with pytest.raises(SyntheticReplayRejected, match="witness integrity"):
        assert_synthetic_history_continues(kept, kept)


def test_reflective_witness_row_container_mutation_is_rejected(tmp_path: Path):
    path = tmp_path / "fixture.sqlite"
    SyntheticOccurrenceStore(path)
    kept = read_synthetic_ledger_witness(path)
    object.__setattr__(kept, "row_hashes", [])
    with pytest.raises(SyntheticReplayRejected, match="witness integrity"):
        kept.assert_integrity()


def test_missing_database_read_does_not_create_empty_file(tmp_path: Path):
    path = tmp_path / "missing.sqlite"
    with pytest.raises(sqlite3.OperationalError):
        read_synthetic_ledger_witness(path)
    assert not path.exists()


def test_uri_special_characters_remain_readonly(tmp_path: Path):
    path = tmp_path / "fixture #1 %.sqlite"
    SyntheticOccurrenceStore(path)
    assert read_synthetic_ledger_witness(path).row_hashes == ()


def test_no_plaintext_token_is_exposed_by_witness(tmp_path: Path):
    path = tmp_path / "fixture.sqlite"
    store = SyntheticOccurrenceStore(path)
    _reserve(store, "private-test-token")
    witness = read_synthetic_ledger_witness(path)
    assert "private-test-token" not in repr(witness)
    assert witness.row_hashes[0] != "synthetic-private-test-token"
