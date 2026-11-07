"""Synthetic WRITE reservations fail closed on malformed SQLite evidence.

Only disposable fixture databases are mutated; these records are neither
human approvals nor authority to dispatch an actual tool backend.
"""

from __future__ import annotations

import hashlib
import sqlite3

import pytest
from test_registry_policy_durable_occurrence_restart_run643 import _fixture

from ark.agency.contracts import Effect, OneShotAuthorization
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)
from ark.agency.registry import ToolRegistration, ToolRegistry


@pytest.mark.parametrize(
    ("column", "value"),
    (
        ("token_digest", "malformed"),
        ("occurrence_id", "occ_not_canonical"),
        ("registry_revision", "tools_malformed"),
        ("bound_action_id", "bound_malformed"),
        ("request_id", "act_malformed"),
        ("reserved_at_ms", 200),
        ("expires_at_ms", 100),
    ),
)
def test_reopened_ledger_quarantines_invalid_stored_row_without_new_reservation(
    tmp_path, column, value,
):
    registry, call, _, token, ledger, occurrence, path, backend = _fixture(tmp_path)
    first = ledger.reserve_synthetic(
        registry, call, token, occurrence_id=occurrence, now_ms=100,
    )
    assert first.dispatch_authorized is False
    with sqlite3.connect(path) as conn:
        conn.execute(
            f"UPDATE synthetic_occurrence_reservations SET {column}=?",
            (value,),
        )
    with pytest.raises(SyntheticReplayRejected, match="row integrity failed"):
        SyntheticOccurrenceStore(path)
    with pytest.raises(SyntheticReplayRejected, match="row integrity failed"):
        ledger.count_synthetic()

    fresh = OneShotAuthorization("fresh-after-corruption", call.request_id, 300)
    new_occurrence = "occ_" + hashlib.sha256(b"fresh-row").hexdigest()
    with pytest.raises(SyntheticReplayRejected, match="row integrity failed"):
        ledger.reserve_synthetic(
            registry, call, fresh, occurrence_id=new_occurrence, now_ms=110,
        )
    with sqlite3.connect(path) as conn:
        assert conn.execute(
            "SELECT COUNT(*) FROM synthetic_occurrence_reservations",
        ).fetchone()[0] == 1
    assert backend.calls == 0


def test_later_deadline_cannot_recycle_expired_token_across_registry_revision(tmp_path):
    registry, call, _, token, ledger, occurrence, path, backend = _fixture(tmp_path)
    receipt = ledger.reserve_synthetic(
        registry, call, token, occurrence_id=occurrence, now_ms=100,
    )
    assert receipt.automatic_replay_authorized is False
    revised = ToolRegistry((
        ToolRegistration(
            "fixture.write", "offline.write", Effect.WRITE, "mock-v2", backend,
        ),
    ))
    assert revised.revision != registry.revision
    extended = OneShotAuthorization(token.token_id, call.request_id, 400)
    next_occurrence = "occ_" + hashlib.sha256(b"later-expiry").hexdigest()
    with pytest.raises(SyntheticReplayRejected, match="already reserved"):
        SyntheticOccurrenceStore(path).reserve_synthetic(
            revised, call, extended, occurrence_id=next_occurrence, now_ms=250,
        )
    assert ledger.count_synthetic() == 1
    assert backend.calls == 0
