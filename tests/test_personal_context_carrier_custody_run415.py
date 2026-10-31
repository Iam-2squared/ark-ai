"""Exact private-context carriers survive every disconnected veto phase.

These are synthetic, privacy-safe fixtures: no model, tool, network, export,
notification, or consent is authorized by an accepted review.
"""

from pathlib import Path

import pytest

import ark.personal_context_revocation_continuity_review as continuity
import ark.personal_context_revocation_review as context
from ark.memory.coherent_snapshot_review import CoherentSnapshotRequest
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_review import ContextSelectionPolicy
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


def _fixture(tmp_path: Path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    store.put(MemoryWrite(
        MemoryScope("fixture-owner", "private"), "source", "PRIVATE-LOCAL-DATA",
    ))
    veto = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    request = CoherentSnapshotRequest(
        "fixture-owner", ("private",), text="PRIVATE",
    )
    policy = ContextSelectionPolicy(3, 3)
    return store, request, policy, veto


def _clone(value: str) -> str:
    result = ("!" + value)[1:]
    assert result == value and result is not value
    return result


@pytest.mark.parametrize("target,field", (
    ("request", "owner_id"),
    ("request", "text"),
    ("policy", "policy_revision"),
))
def test_first_veto_continuity_cannot_rebind_equal_private_input(
    tmp_path: Path, monkeypatch, target: str, field: str,
):
    state = _fixture(tmp_path)
    original = continuity.review_revocation_continuity
    calls = []

    def changed(*args, **kwargs):
        witness = original(*args, **kwargs)
        calls.append(1)
        obj = state[1] if target == "request" else state[2]
        object.__setattr__(obj, field, _clone(getattr(obj, field)))
        return witness

    monkeypatch.setattr(continuity, "review_revocation_continuity", changed)
    with pytest.raises(context.SyntheticContextRevocationRejected, match="context source"):
        context.review_fresh_nonrevoked_context(state[0], state[1], state[2], state[3])
    assert calls == [1]


def test_first_veto_cannot_rebind_equal_scope_namespace(tmp_path: Path, monkeypatch):
    state = _fixture(tmp_path)
    original = SyntheticContextRevocationLedger.assert_not_revoked
    calls = []

    def changed(self, scopes):
        original(self, scopes)
        calls.append(1)
        object.__setattr__(scopes[0], "namespace", _clone(scopes[0].namespace))

    monkeypatch.setattr(SyntheticContextRevocationLedger, "assert_not_revoked", changed)
    with pytest.raises(context.SyntheticContextRevocationRejected, match="context source"):
        context.review_fresh_nonrevoked_context(state[0], state[1], state[2], state[3])
    assert calls == [1]


def test_clean_context_remains_private_and_non_authorizing(tmp_path: Path):
    store, request, policy, veto = _fixture(tmp_path)
    bundle = context.review_fresh_nonrevoked_context(store, request, policy, veto)
    assert [item.content for item in bundle.items] == ["PRIVATE-LOCAL-DATA"]
    assert bundle.action_authorized is False
    assert bundle.dispatch_authorized is False
