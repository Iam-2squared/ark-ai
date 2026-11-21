"""A fresh private Context bundle cannot be rewritten by final veto callbacks.

Only disposable local SQLite fixtures are used. Passing these synthetic veto
checks is never authenticated consent, privacy clearance or export authority.
"""

from dataclasses import replace
from pathlib import Path

import pytest

import ark.personal_context_revocation_continuity_review as continuity
import ark.personal_context_revocation_review as context
from ark.memory.coherent_snapshot_review import CoherentSnapshotRequest
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_review import ContextSelectionPolicy


def _setup(tmp_path: Path):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    memory.put(MemoryWrite(MemoryScope("offline-owner", "profile"), "name", "safe"))
    ledger = context.SyntheticContextRevocationLedger(
        tmp_path / "privacy-veto.sqlite",
    )
    request = CoherentSnapshotRequest("offline-owner", ("profile",))
    return memory, ledger, request, ContextSelectionPolicy(2, 2)


def _mutation(bundle, case):
    item = bundle.items[0]
    if case == "content":
        object.__setattr__(item, "content", "forged-private-context")
    elif case == "namespace":
        object.__setattr__(item, "namespace", "other-scope")
    elif case == "same-content-carrier":
        cloned = item.content.encode("utf-8").decode("utf-8")
        assert cloned == item.content and cloned is not item.content
        object.__setattr__(item, "content", cloned)
    elif case == "same-item-clone":
        object.__setattr__(bundle, "items", (replace(item),))
    elif case == "same-tuple-clone":
        cloned = tuple(list(bundle.items))
        assert cloned == bundle.items and cloned is not bundle.items
        object.__setattr__(bundle, "items", cloned)
    elif case == "same-digest-clone":
        original = bundle.snapshot_digest
        cloned = original.encode("ascii").decode("ascii")
        assert cloned == original and cloned is not original
        object.__setattr__(bundle, "snapshot_digest", cloned)
    else:
        raise AssertionError(f"unknown synthetic mutation: {case}")


@pytest.mark.parametrize(
    "case",
    (
        "content", "namespace", "same-content-carrier",
        "same-item-clone", "same-tuple-clone", "same-digest-clone",
    ),
)
def test_final_veto_callback_cannot_rewrite_private_projection(
    tmp_path: Path, monkeypatch, case: str,
):
    memory, ledger, request, policy = _setup(tmp_path)
    captured = []
    project = context.review_personal_context
    veto = ledger.assert_not_revoked
    calls = []

    def observe(snapshot, selector):
        result = project(snapshot, selector)
        captured.append(result)
        return result

    def inspect(scopes):
        veto(scopes)
        calls.append(True)
        if len(calls) == 2:
            _mutation(captured[0], case)

    monkeypatch.setattr(context, "review_personal_context", observe)
    monkeypatch.setattr(ledger, "assert_not_revoked", inspect)
    with pytest.raises(
        context.SyntheticContextRevocationRejected,
        match="context bundle changed",
    ):
        context.review_fresh_nonrevoked_context(
            memory, request, policy, ledger,
        )
    assert len(captured) == 1
    assert len(calls) == 2


def test_retained_history_callback_cannot_rewrite_projection_after_veto(
    tmp_path: Path, monkeypatch,
):
    memory, ledger, request, policy = _setup(tmp_path)
    captured = []
    project = context.review_personal_context
    review = continuity.review_revocation_continuity
    calls = []

    def observe(snapshot, selector):
        result = project(snapshot, selector)
        captured.append(result)
        return result

    def inspect(*args, **kwargs):
        result = review(*args, **kwargs)
        calls.append(True)
        if len(calls) == 2:
            object.__setattr__(captured[0].items[0], "content", "late-forgery")
        return result

    monkeypatch.setattr(context, "review_personal_context", observe)
    monkeypatch.setattr(continuity, "review_revocation_continuity", inspect)
    with pytest.raises(
        context.SyntheticContextRevocationRejected,
        match="context bundle changed",
    ):
        context.review_fresh_nonrevoked_context(
            memory, request, policy, ledger,
        )
    assert len(captured) == 1
    assert len(calls) == 2


def test_stable_veto_retained_history_preserves_private_bundle_inertness(
    tmp_path: Path,
):
    memory, ledger, request, policy = _setup(tmp_path)
    retained = continuity.review_revocation_continuity(ledger)
    result = context.review_fresh_nonrevoked_context(
        memory, request, policy, ledger, retained_revocations=retained,
    )
    assert [item.content for item in result.items] == ["safe"]
    assert result.action_authorized is False
    assert result.dispatch_authorized is False
