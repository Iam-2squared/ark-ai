"""A retained Context veto prefix must survive the entire reuse review.

Local-only privacy fixtures: no permission, deletion, or content disclosure.
"""

from pathlib import Path

import pytest

import ark.personal_context_reuse_review as reuse
from ark.memory.coherent_snapshot_review import CoherentSnapshotRequest
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_review import ContextSelectionPolicy
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    review_fresh_nonrevoked_context,
)


def _state(tmp_path: Path):
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("owner", "profile")
    store.put(MemoryWrite(scope, "fixture", "PRIVATE-CONTENT"))
    request = CoherentSnapshotRequest("owner", ("profile",))
    policy = ContextSelectionPolicy(4, 4)
    ledger = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    before = review_revocation_continuity(ledger)
    cached = review_fresh_nonrevoked_context(store, request, policy, ledger)
    # A newer independently valid prefix for an unrelated owner provides a
    # detectable reflected witness substitution, without revoking 'profile'.
    ledger.revoke(MemoryScope("another", "unrelated"), at_ms=10)
    after = review_revocation_continuity(ledger)
    return (store, request, policy, ledger, cached), before, after


def _review(state, retained):
    return reuse.review_synthetic_context_reuse(
        *state, captured_at_ms=100, now_ms=101, max_age_ms=10,
        retained_revocations=retained,
    )


def test_untouched_earlier_veto_prefix_is_inert(tmp_path: Path):
    state, retained, _after = _state(tmp_path)
    result = _review(state, retained)
    assert result.context_use_authorized is False
    assert result.external_disclosure_authorized is False
    assert result.dispatch_authorized is False
    assert "PRIVATE-CONTENT" not in repr(result)


def test_invalid_retained_witness_type_is_denied(tmp_path: Path):
    state, _before, _after = _state(tmp_path)
    with pytest.raises(reuse.SyntheticContextReuseRejected, match="exact retained"):
        _review(state, object())


@pytest.mark.parametrize("corrupt", ["valid_other_prefix", "malformed_identity"])
def test_reentrant_retained_veto_replacement_after_projection_is_denied(
    tmp_path: Path, monkeypatch, corrupt: str,
):
    state, retained, newer = _state(tmp_path)
    original = reuse.review_fresh_nonrevoked_context

    def change_after_projection(*args, **kwargs):
        fresh = original(*args, **kwargs)
        object.__setattr__(retained, "rows", newer.rows)
        object.__setattr__(
            retained, "witness_id",
            newer.witness_id if corrupt == "valid_other_prefix" else "invalid",
        )
        return fresh

    monkeypatch.setattr(
        reuse, "review_fresh_nonrevoked_context", change_after_projection,
    )
    with pytest.raises(RuntimeError, match="retained|revocation"):
        _review(state, retained)
