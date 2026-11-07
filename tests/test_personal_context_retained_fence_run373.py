"""Fresh context projection rejects missing retained privacy veto history."""

import sqlite3
from pathlib import Path

import pytest

from ark.memory.coherent_snapshot_review import CoherentSnapshotRequest
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_review import ContextSelectionPolicy
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
    review_fresh_nonrevoked_context,
)


def _setup(tmp_path: Path, clock):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=clock)
    memory.put(MemoryWrite(MemoryScope("owner", "profile"), "name", "fixture"))
    ledger = SyntheticContextRevocationLedger(tmp_path / "revoke.sqlite")
    ledger.revoke(MemoryScope("owner", "notes"), at_ms=100)
    return memory, ledger, CoherentSnapshotRequest("owner", ("profile",))


def test_earlier_retained_veto_blocks_silent_deletion(tmp_path: Path):
    memory, ledger, request = _setup(tmp_path, lambda: 100)
    witness = review_revocation_continuity(ledger)
    with sqlite3.connect(ledger.path) as conn:
        conn.execute("DELETE FROM synthetic_context_revocations")
    with pytest.raises(SyntheticContextRevocationRejected, match="history changed"):
        review_fresh_nonrevoked_context(
            memory, request, ContextSelectionPolicy(2, 2), ledger,
            retained_revocations=witness,
        )


def test_unrelated_revocation_deletion_during_read_is_detected(tmp_path: Path):
    flag = {"delete": False}
    holder = []

    def clock():
        if flag["delete"]:
            flag["delete"] = False
            with sqlite3.connect(holder[0].path) as conn:
                conn.execute("DELETE FROM synthetic_context_revocations")
        return 100

    memory, ledger, request = _setup(tmp_path, clock)
    holder.append(ledger)
    flag["delete"] = True
    with pytest.raises(SyntheticContextRevocationRejected, match="history changed"):
        review_fresh_nonrevoked_context(
            memory, request, ContextSelectionPolicy(2, 2), ledger,
        )


def test_new_unrelated_veto_during_review_is_allowed_without_authority(
    tmp_path: Path,
):
    flag = {"add": False}
    holder = []

    def clock():
        if flag["add"]:
            flag["add"] = False
            holder[0].revoke(MemoryScope("owner", "other"), at_ms=101)
        return 100

    memory, ledger, request = _setup(tmp_path, clock)
    flag["add"] = True
    holder.append(ledger)
    result = review_fresh_nonrevoked_context(
        memory, request, ContextSelectionPolicy(2, 2), ledger,
    )
    assert [item.content for item in result.items] == ["fixture"]
    assert result.action_authorized is False
    assert len(review_revocation_continuity(ledger).rows) == 2


def test_fake_retained_privacy_witness_is_refused(tmp_path: Path):
    memory, ledger, request = _setup(tmp_path, lambda: 100)
    with pytest.raises(SyntheticContextRevocationRejected, match="exact retained"):
        review_fresh_nonrevoked_context(
            memory, request, ContextSelectionPolicy(2, 2), ledger,
            retained_revocations=object(),
        )
