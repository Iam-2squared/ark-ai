"""Local privacy reuse: denial-only result descriptors are not callback authority.

All data are synthetic SQLite fixtures. No consent, external export or Tool
execution is inferred from a successful content-free diagnostic receipt.
"""

from __future__ import annotations

import pytest

import ark.personal_context_reuse_review as reuse
from ark.memory.coherent_snapshot_review import CoherentSnapshotRequest
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_review import ContextSelectionPolicy
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    review_fresh_nonrevoked_context,
)


def _state(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "context-memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("fixture-owner", "profile")
    store.put(MemoryWrite(scope, "source", "synthetic-private"))
    request = CoherentSnapshotRequest("fixture-owner", ("profile",))
    policy = ContextSelectionPolicy(2, 2)
    ledger = SyntheticContextRevocationLedger(tmp_path / "context-veto.sqlite")
    cached = review_fresh_nonrevoked_context(store, request, policy, ledger)
    return store, request, policy, ledger, cached


def _review(state):
    return reuse.review_synthetic_context_reuse(
        *state, captured_at_ms=100, now_ms=100, max_age_ms=0,
    )


@pytest.mark.parametrize(
    "name",
    (
        "bundle_id", "snapshot_digest", "rechecked_at_ms",
        "context_use_authorized", "external_disclosure_authorized",
        "dispatch_authorized", "__init__", "__getattribute__",
    ),
)
def test_counterfeit_result_carrier_rejected_before_private_projection(
    tmp_path, monkeypatch, name,
):
    state = _state(tmp_path)
    callbacks = []

    class Counterfeit:
        def __get__(self, *args):
            callbacks.append(name)
            return False

    def forbidden_projection(*args, **kwargs):
        callbacks.append("private projection")
        raise AssertionError("private SQLite projection must not run")

    monkeypatch.setattr(reuse, "review_fresh_nonrevoked_context", forbidden_projection)
    monkeypatch.setattr(reuse.SyntheticContextReuseReview, name, Counterfeit())
    with pytest.raises(reuse.SyntheticContextReuseRejected, match="receipt carrier changed"):
        _review(state)
    assert callbacks == []


def test_result_class_rebound_to_authorizing_object_is_rejected(
    tmp_path, monkeypatch,
):
    state = _state(tmp_path)
    original = reuse.SyntheticContextReuseReview

    class Counterfeit:
        def __init__(self, *args):
            self.bundle_id, self.snapshot_digest, self.rechecked_at_ms = args

        @property
        def context_use_authorized(self):
            return True

    def forbidden_projection(*_args, **_kwargs):
        pytest.fail("counterfeit result class reached private Memory projection")

    monkeypatch.setattr(reuse, "SyntheticContextReuseReview", Counterfeit)
    monkeypatch.setattr(
        reuse, "review_fresh_nonrevoked_context", forbidden_projection,
    )
    with pytest.raises(
        reuse.SyntheticContextReuseRejected,
        match="receipt carrier changed",
    ):
        _review(state)
    assert original is not Counterfeit


def test_receipt_authority_flag_rebound_after_projection_is_denied(
    tmp_path, monkeypatch,
):
    state = _state(tmp_path)
    original = reuse.review_fresh_nonrevoked_context

    class Counterfeit:
        def __get__(self, *args):
            raise AssertionError("untrusted authority property was invoked")

    def project_then_rebind(*args, **kwargs):
        result = original(*args, **kwargs)
        monkeypatch.setattr(
            reuse.SyntheticContextReuseReview,
            "external_disclosure_authorized",
            Counterfeit(),
        )
        return result

    monkeypatch.setattr(reuse, "review_fresh_nonrevoked_context", project_then_rebind)
    with pytest.raises(reuse.SyntheticContextReuseRejected, match="receipt carrier changed"):
        _review(state)


def test_unmodified_reuse_receipt_retains_three_denials(tmp_path):
    result = _review(_state(tmp_path))
    assert result.context_use_authorized is False
    assert result.external_disclosure_authorized is False
    assert result.dispatch_authorized is False
    assert "synthetic-private" not in repr(result)
