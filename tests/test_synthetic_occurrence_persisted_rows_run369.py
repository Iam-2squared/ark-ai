"""Persisted synthetic reservation rows are untrusted, even under intact schema.

These fixtures never attest an issuer or enable a real Tool backend.
"""

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


class NeverExecuted:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("no synthetic review may dispatch a backend")


def _identity():
    registry = ToolRegistry(
        (ToolRegistration("mock_tool", "fixture", Effect.WRITE, "offline", NeverExecuted()),)
    )
    call = ToolCall("mock_tool", "fixture", "synthetic", {"number": 1})
    return registry, call


def _occurrence(name: str) -> str:
    return "occ_" + hashlib.sha256(name.encode()).hexdigest()


def _initial(path: Path) -> SyntheticOccurrenceStore:
    store = SyntheticOccurrenceStore(path)
    registry, call = _identity()
    store.reserve_synthetic(
        registry, call,
        OneShotAuthorization("artificial-token-a", call.request_id, 1000),
        occurrence_id=_occurrence("first"), now_ms=20,
    )
    return store


@pytest.mark.parametrize(
    ("column", "replacement"),
    [
        ("token_digest", "INVALID"),
        ("occurrence_id", "occ_invalid"),
        ("registry_revision", "tools_invalid"),
        ("bound_action_id", "bound_invalid"),
        ("request_id", "act_invalid"),
        ("reserved_at_ms", "not-a-timestamp"),
        ("expires_at_ms", "not-a-timestamp"),
        ("expires_at_ms", 20),
        ("reserved_at_ms", 1000),
    ],
)
def test_corrupt_fixture_row_rejected_on_open_read_and_next_reserve(
    tmp_path: Path, column: str, replacement: object,
):
    path = tmp_path / "fixture.sqlite"
    store = _initial(path)
    assert store.count_synthetic() == 1
    # Only column names from the fixed parameter list above are used here.
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE synthetic_occurrence_reservations SET {column}=?",
            (replacement,),
        )
    with pytest.raises(SyntheticReplayRejected):
        SyntheticOccurrenceStore(path)
    with pytest.raises(SyntheticReplayRejected):
        store.count_synthetic()
    registry, call = _identity()
    with pytest.raises(SyntheticReplayRejected):
        store.reserve_synthetic(
            registry, call,
            OneShotAuthorization("artificial-token-b", call.request_id, 1000),
            occurrence_id=_occurrence("second"), now_ms=21,
        )
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM synthetic_occurrence_reservations"
        ).fetchone()[0] == 1


def test_valid_fixture_row_survives_restart_and_readonly_review(tmp_path: Path):
    path = tmp_path / "fixture.sqlite"
    _initial(path)
    second = SyntheticOccurrenceStore(path)
    assert second.count_synthetic() == 1
    registry, call = _identity()
    receipt = second.reserve_synthetic(
        registry, call,
        OneShotAuthorization("artificial-token-b", call.request_id, 1000),
        occurrence_id=_occurrence("second"), now_ms=999,
    )
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert second.count_synthetic() == 2
