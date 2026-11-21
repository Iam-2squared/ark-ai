"""A separate process can commit a privacy veto during context projection.

The second on-disk privacy check must detect a newly revoked requested
scope. An unrelated owner may change independently, but the resulting
local bundle never conveys consent, export or tool execution authority.
"""

from __future__ import annotations

import os
from multiprocessing import get_context
from pathlib import Path

import pytest

import ark.personal_context_revocation_review as context
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.coherent_snapshot_review import CoherentSnapshotRequest
from ark.personal_context_review import ContextSelectionPolicy
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


def _revoke_in_other_interpreter(path: str, owner: str) -> None:
    ledger = SyntheticContextRevocationLedger(Path(path))
    ledger.revoke(MemoryScope(owner, "profile"), at_ms=101)
    os._exit(0)  # Veto COMMIT remains despite lost acknowledgement.


@pytest.mark.parametrize("revoked_owner", ("private-owner", "unrelated-owner"))
def test_process_committed_veto_between_projection_and_final_check(
    tmp_path, monkeypatch, revoked_owner,
):
    memory = SQLiteMemoryStore(tmp_path / "context-memory.sqlite", clock_ms=lambda: 100)
    requested = MemoryScope("private-owner", "profile")
    memory.put(MemoryWrite(requested, "seed", "sensitive fixture text"))
    ledger = SyntheticContextRevocationLedger(tmp_path / "context-veto.sqlite")
    request = CoherentSnapshotRequest("private-owner", ("profile",))
    policy = ContextSelectionPolicy(3, 3)
    original_project = context.review_personal_context
    spawned = []

    def project_then_commit_elsewhere(snapshot, original_policy):
        projected = original_project(snapshot, original_policy)
        worker = get_context("spawn").Process(
            target=_revoke_in_other_interpreter,
            args=(str(ledger.path), revoked_owner),
        )
        worker.start()
        worker.join(timeout=35)
        if worker.is_alive():
            worker.terminate()
            worker.join(timeout=5)
        assert worker.exitcode == 0, "privacy worker did not commit the veto"
        spawned.append(True)
        return projected

    monkeypatch.setattr(context, "review_personal_context", project_then_commit_elsewhere)
    if revoked_owner == "private-owner":
        with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
            context.review_fresh_nonrevoked_context(memory, request, policy, ledger)
    else:
        result = context.review_fresh_nonrevoked_context(
            memory, request, policy, ledger,
        )
        assert tuple(item.content for item in result.items) == (
            "sensitive fixture text",
        )
        assert result.action_authorized is False
        assert result.dispatch_authorized is False
    assert spawned == [True]
    cold = SyntheticContextRevocationLedger(ledger.path)
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        cold.assert_not_revoked((MemoryScope(revoked_owner, "profile"),))
    assert b"private-owner" not in ledger.path.read_bytes()
    assert b"unrelated-owner" not in ledger.path.read_bytes()
