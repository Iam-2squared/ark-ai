"""Privacy veto must inspect the exact namespaces selected for Memory.

The callback is deliberately hostile, but no Context is exported, deleted,
notified or passed to a model/backend by these synthetic tests.
"""

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


def _fixture(tmp_path: Path):
    owner, namespace = "fixture-owner", "private"
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope(owner, namespace)
    memory.put(MemoryWrite(scope, "source", "not-for-export"))
    ledger = SyntheticContextRevocationLedger(tmp_path / "revocations.sqlite")
    request = CoherentSnapshotRequest(owner, (namespace,))
    return memory, scope, ledger, request, ContextSelectionPolicy(2, 2)


@pytest.mark.parametrize("field,decoy", (
    ("owner_id", "someone-else"),
    ("namespace", "unrevoked-decoy"),
))
def test_first_veto_cannot_be_redirected_away_from_revoked_scope(
    tmp_path: Path, monkeypatch, field: str, decoy: str,
):
    memory, scope, ledger, request, policy = _fixture(tmp_path)
    ledger.revoke(scope, at_ms=101)
    original = SyntheticContextRevocationLedger.assert_not_revoked
    calls = 0

    def retarget(self, scopes):
        nonlocal calls
        calls += 1
        object.__setattr__(scopes[0], field, decoy)
        return original(self, scopes)

    monkeypatch.setattr(
        SyntheticContextRevocationLedger, "assert_not_revoked", retarget,
    )
    with pytest.raises(SyntheticContextRevocationRejected, match="context source"):
        review_fresh_nonrevoked_context(memory, request, policy, ledger)
    assert calls == 1


@pytest.mark.parametrize("field,decoy", (
    ("owner_id", "someone-else"),
    ("namespace", "unrevoked-decoy"),
))
def test_second_veto_scope_mutation_is_rejected(
    tmp_path: Path, monkeypatch, field: str, decoy: str,
):
    memory, _scope, ledger, request, policy = _fixture(tmp_path)
    original = SyntheticContextRevocationLedger.assert_not_revoked
    calls = 0

    def retarget_on_second(self, scopes):
        nonlocal calls
        calls += 1
        if calls == 2:
            object.__setattr__(scopes[0], field, decoy)
        return original(self, scopes)

    monkeypatch.setattr(
        SyntheticContextRevocationLedger, "assert_not_revoked",
        retarget_on_second,
    )
    with pytest.raises(SyntheticContextRevocationRejected, match="context source"):
        review_fresh_nonrevoked_context(memory, request, policy, ledger)
    assert calls == 2


def test_equal_value_namespace_tuple_replacement_is_rejected(
    tmp_path: Path, monkeypatch,
):
    memory, _scope, ledger, request, policy = _fixture(tmp_path)
    original = SyntheticContextRevocationLedger.assert_not_revoked

    def replace_request_carrier(self, scopes):
        result = original(self, scopes)
        replacement = tuple(list(request.namespaces))
        assert replacement == request.namespaces
        assert replacement is not request.namespaces
        object.__setattr__(request, "namespaces", replacement)
        return result

    monkeypatch.setattr(
        SyntheticContextRevocationLedger, "assert_not_revoked",
        replace_request_carrier,
    )
    with pytest.raises(SyntheticContextRevocationRejected, match="context source"):
        review_fresh_nonrevoked_context(memory, request, policy, ledger)


def test_unchanged_scopes_still_return_only_inert_projection(tmp_path: Path):
    memory, _scope, ledger, request, policy = _fixture(tmp_path)
    bundle = review_fresh_nonrevoked_context(memory, request, policy, ledger)
    assert [item.content for item in bundle.items] == ["not-for-export"]
    assert bundle.action_authorized is False
    assert bundle.dispatch_authorized is False
