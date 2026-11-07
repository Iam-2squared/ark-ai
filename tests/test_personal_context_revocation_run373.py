"""Offline revocation veto persists and brackets fresh Personal Context reads."""

import sqlite3
from pathlib import Path

import pytest

from ark.memory.coherent_snapshot_review import CoherentSnapshotRequest
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_review import ContextSelectionPolicy
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
    review_fresh_nonrevoked_context,
)


def _fixtures(tmp_path, *, clock=None):
    now = (lambda: 100) if clock is None else clock
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=now)
    scope = MemoryScope("private-owner", "profile")
    memory.put(MemoryWrite(scope, "name", "first"))
    ledger = SyntheticContextRevocationLedger(tmp_path / "veto #100 %.sqlite")
    request = CoherentSnapshotRequest("private-owner", ("profile",))
    policy = ContextSelectionPolicy(3, 3)
    return memory, scope, ledger, request, policy


def test_fresh_projection_is_inert_and_reflects_new_memory_revision(tmp_path: Path):
    memory, scope, ledger, request, policy = _fixtures(tmp_path)
    first = review_fresh_nonrevoked_context(memory, request, policy, ledger)
    assert [item.content for item in first.items] == ["first"]
    assert first.action_authorized is False
    assert first.dispatch_authorized is False
    memory.put(MemoryWrite(scope, "name", "second"), expected_revision=1)
    second = review_fresh_nonrevoked_context(memory, request, policy, ledger)
    assert [item.content for item in second.items] == ["second"]
    assert first.bundle_id != second.bundle_id


def test_revoke_persists_across_restart_and_does_not_store_plaintext(tmp_path: Path):
    memory, scope, ledger, request, policy = _fixtures(tmp_path)
    marker = ledger.revoke(scope, at_ms=101)
    assert len(marker) == 64
    with sqlite3.connect(ledger.path) as conn:
        rows = conn.execute("SELECT * FROM synthetic_context_revocations").fetchall()
    assert "private-owner" not in repr(rows)
    assert "profile" not in repr(rows)
    reopened = SyntheticContextRevocationLedger(ledger.path)
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        review_fresh_nonrevoked_context(memory, request, policy, reopened)


def test_scope_veto_does_not_block_unrelated_namespace(tmp_path: Path):
    memory, scope, ledger, _request, policy = _fixtures(tmp_path)
    other = MemoryScope("private-owner", "notes")
    memory.put(MemoryWrite(other, "note", "safe"))
    ledger.revoke(scope, at_ms=101)
    projection = review_fresh_nonrevoked_context(
        memory, CoherentSnapshotRequest("private-owner", ("notes",)),
        policy, ledger,
    )
    assert [item.content for item in projection.items] == ["safe"]
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        review_fresh_nonrevoked_context(
            memory, CoherentSnapshotRequest("private-owner", ("notes", "profile")),
            policy, ledger,
        )


def test_clock_callback_revocation_during_memory_read_is_detected(tmp_path: Path):
    state = {"revoke": False}
    scope = MemoryScope("private-owner", "profile")
    holder = []

    def clock():
        if state["revoke"]:
            state["revoke"] = False
            holder[0].revoke(scope, at_ms=101)
        return 100

    memory, _scope, ledger, request, policy = _fixtures(tmp_path, clock=clock)
    holder.append(ledger)
    state["revoke"] = True
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        review_fresh_nonrevoked_context(memory, request, policy, ledger)


@pytest.mark.parametrize("bad", [True, -1, 2**63, "100"])
def test_invalid_revocation_clock_never_writes(tmp_path: Path, bad):
    _memory, scope, ledger, _request, _policy = _fixtures(tmp_path)
    with pytest.raises(SyntheticContextRevocationRejected, match="timestamp"):
        ledger.revoke(scope, at_ms=bad)
    ledger.assert_not_revoked((scope,))


def test_duplicate_revocation_and_clock_rollback_are_denied(tmp_path: Path):
    _memory, scope, ledger, _request, _policy = _fixtures(tmp_path)
    ledger.revoke(scope, at_ms=101)
    with pytest.raises(SyntheticContextRevocationRejected, match="already revoked"):
        ledger.revoke(scope, at_ms=102)
    with pytest.raises(SyntheticContextRevocationRejected, match="clock regressed"):
        ledger.revoke(MemoryScope("private-owner", "notes"), at_ms=100)


def test_expired_request_mode_is_never_projected(tmp_path: Path):
    memory, _scope, ledger, _request, policy = _fixtures(tmp_path)
    with pytest.raises(SyntheticContextRevocationRejected, match="expired records"):
        review_fresh_nonrevoked_context(
            memory, CoherentSnapshotRequest(
                "private-owner", ("profile",), include_expired=True,
            ), policy, ledger,
        )


def test_missing_veto_store_is_never_recreated(tmp_path: Path):
    _memory, scope, ledger, _request, _policy = _fixtures(tmp_path)
    ledger.path.unlink()
    with pytest.raises(sqlite3.OperationalError):
        ledger.assert_not_revoked((scope,))
    assert not ledger.path.exists()


def test_valid_shape_but_rewritten_digest_refused(tmp_path: Path):
    _memory, scope, ledger, _request, _policy = _fixtures(tmp_path)
    ledger.revoke(scope, at_ms=101)
    with sqlite3.connect(ledger.path) as conn:
        conn.execute("UPDATE synthetic_context_revocations SET scope_digest='bad'")
    with pytest.raises(SyntheticContextRevocationRejected, match="row integrity"):
        ledger.assert_not_revoked((scope,))


def test_schema_drift_refused_without_repair(tmp_path: Path):
    _memory, scope, ledger, _request, _policy = _fixtures(tmp_path)
    with sqlite3.connect(ledger.path) as conn:
        conn.execute("PRAGMA user_version=2")
    with pytest.raises(SyntheticContextRevocationRejected, match="schema version"):
        ledger.assert_not_revoked((scope,))
