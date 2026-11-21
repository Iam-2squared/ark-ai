"""Private context review must retain the first revocation witness epoch.

All revocations and context records are local fixtures; review is deny-only.
"""

import pytest

import ark.personal_context_revocation_continuity_review as continuity
from ark.memory.coherent_snapshot_review import CoherentSnapshotRequest
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_review import ContextSelectionPolicy
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
    review_fresh_nonrevoked_context,
)


def _setup(tmp_path):
    memory = SQLiteMemoryStore(tmp_path / "mem.sqlite", clock_ms=lambda: 100)
    memory.put(MemoryWrite(MemoryScope("owner", "profile"), "entry", "fixture"))
    ledger = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    ledger.revoke(MemoryScope("owner", "unrelated"), at_ms=50)
    return memory, CoherentSnapshotRequest(
        "owner", ("profile",),
    ), ContextSelectionPolicy(2, 2), ledger


def _clone(value):
    duplicate = ("!" + value)[1:]
    assert duplicate == value and duplicate is not value
    return duplicate


@pytest.mark.parametrize("variant", (
    "first_veto_equal_id",
    "second_veto_equal_rows",
    "final_recheck_equal_id",
))
def test_unrelated_veto_must_keep_first_witness_object_epoch(
    tmp_path, monkeypatch, variant,
):
    store, request, policy, ledger = _setup(tmp_path)
    original_review = continuity.review_revocation_continuity
    original_veto = SyntheticContextRevocationLedger.assert_not_revoked
    seen = []
    checks = []

    def capture(checked_ledger, *, retained=None):
        result = original_review(checked_ledger, retained=retained)
        if retained is None:
            seen.append(result)
        if variant == "final_recheck_equal_id" and retained is not None:
            object.__setattr__(retained, "witness_id", _clone(retained.witness_id))
        return result

    def mutable_veto(self, scopes):
        original_veto(self, scopes)
        checks.append(True)
        if variant == "first_veto_equal_id" and len(checks) == 1:
            object.__setattr__(seen[0], "witness_id", _clone(seen[0].witness_id))
        if variant == "second_veto_equal_rows" and len(checks) == 2:
            previous = seen[0].rows
            duplicate = tuple(list(previous))
            assert duplicate == previous and duplicate is not previous
            object.__setattr__(seen[0], "rows", duplicate)

    monkeypatch.setattr(continuity, "review_revocation_continuity", capture)
    monkeypatch.setattr(
        SyntheticContextRevocationLedger, "assert_not_revoked", mutable_veto,
    )
    with pytest.raises(
        SyntheticContextRevocationRejected,
        match="context source, request or policy changed",
    ):
        review_fresh_nonrevoked_context(store, request, policy, ledger)
    assert len(seen) == 1
    assert checks


def test_unchanged_veto_witness_preserves_deny_only_context(tmp_path):
    store, request, policy, ledger = _setup(tmp_path)
    bundle = review_fresh_nonrevoked_context(store, request, policy, ledger)
    assert [item.content for item in bundle.items] == ["fixture"]
    assert bundle.action_authorized is False
