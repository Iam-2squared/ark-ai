"""Cached Personal Context never bypasses fresh Memory and privacy veto checks."""

import sqlite3
from dataclasses import replace
from pathlib import Path

import pytest

from ark.memory.coherent_snapshot_review import CoherentSnapshotRequest
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_reuse_review import (
    SyntheticContextReuseRejected,
    review_synthetic_context_reuse,
)
from ark.personal_context_review import ContextSelectionPolicy
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
    review_fresh_nonrevoked_context,
)


def _setup(path: Path):
    memory = SQLiteMemoryStore(path / "memory.sqlite", clock_ms=lambda: 100)
    scope = MemoryScope("owner", "profile")
    memory.put(MemoryWrite(scope, "identity", "synthetic only"))
    request = CoherentSnapshotRequest("owner", ("profile",))
    policy = ContextSelectionPolicy(2, 2)
    ledger = SyntheticContextRevocationLedger(path / "veto #1 %.sqlite")
    cached = review_fresh_nonrevoked_context(memory, request, policy, ledger)
    return memory, request, policy, ledger, cached, scope


def _review(state, **overrides):
    memory, request, policy, ledger, cached, _scope = state
    kw = dict(captured_at_ms=100, now_ms=100, max_age_ms=10)
    kw.update(overrides)
    return review_synthetic_context_reuse(
        memory, request, policy, ledger, cached, **kw,
    )


def test_fresh_revalidation_returns_only_content_free_inert_receipt(tmp_path: Path):
    state = _setup(tmp_path)
    result = _review(state)
    assert result.bundle_id == state[4].bundle_id
    assert result.snapshot_digest == state[4].snapshot_digest
    assert result.rechecked_at_ms == 100
    assert result.context_use_authorized is False
    assert result.external_disclosure_authorized is False
    assert result.dispatch_authorized is False
    assert "synthetic only" not in repr(result)


def test_exact_ttl_boundary_passes_but_expired_cache_fails(tmp_path: Path):
    state = _setup(tmp_path)
    assert _review(state, now_ms=110).rechecked_at_ms == 110
    with pytest.raises(SyntheticContextReuseRejected, match="age or clock"):
        _review(state, now_ms=111)


@pytest.mark.parametrize("bad", [True, -1, 2**63, "100"])
def test_untrusted_now_must_be_exact_sqlite_integer(tmp_path: Path, bad):
    state = _setup(tmp_path)
    with pytest.raises(SyntheticContextReuseRejected, match="synthetic context|age"):
        _review(state, now_ms=bad)


def test_clock_rollback_fails_closed(tmp_path: Path):
    state = _setup(tmp_path)
    with pytest.raises(SyntheticContextReuseRejected, match="clock"):
        _review(state, now_ms=99)


def test_invalid_ttl_and_capture_are_rejected(tmp_path: Path):
    state = _setup(tmp_path)
    with pytest.raises(SyntheticContextReuseRejected, match="age or clock"):
        _review(state, max_age_ms=-1)
    with pytest.raises(SyntheticContextReuseRejected, match="exact synthetic"):
        _review(state, captured_at_ms=False)


def test_memory_revision_change_blocks_cached_context(tmp_path: Path):
    state = _setup(tmp_path)
    state[0].put(
        MemoryWrite(state[5], "identity", "new synthetic"),
        expected_revision=1,
    )
    with pytest.raises(SyntheticContextReuseRejected, match="differs from fresh"):
        _review(state)


def test_revocation_after_capture_is_detected(tmp_path: Path):
    state = _setup(tmp_path)
    state[3].revoke(state[5], at_ms=101)
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        _review(state)


def test_unrelated_revocation_does_not_grant_authority(tmp_path: Path):
    state = _setup(tmp_path)
    state[3].revoke(MemoryScope("owner", "unrelated"), at_ms=101)
    result = _review(state)
    assert result.context_use_authorized is False
    assert result.external_disclosure_authorized is False


def test_retained_privacy_veto_detects_silent_marker_deletion(tmp_path: Path):
    state = _setup(tmp_path)
    state[3].revoke(MemoryScope("owner", "notes"), at_ms=101)
    witness = review_revocation_continuity(state[3])
    with sqlite3.connect(state[3].path) as conn:
        conn.execute("DELETE FROM synthetic_context_revocations")
    with pytest.raises(SyntheticContextRevocationRejected, match="history changed"):
        _review(state, retained_revocations=witness)


def test_forged_cached_bundle_id_is_rejected(tmp_path: Path):
    state = _setup(tmp_path)
    wrong = replace(state[4], bundle_id="ctx_bundle_" + "f" * 64)
    with pytest.raises(SyntheticContextReuseRejected, match="differs from fresh"):
        review_synthetic_context_reuse(
            state[0], state[1], state[2], state[3], wrong,
            captured_at_ms=100, now_ms=100, max_age_ms=10,
        )


def test_invalid_cached_type_rejected_without_memory_use(tmp_path: Path):
    state = _setup(tmp_path)
    with pytest.raises(SyntheticContextReuseRejected, match="exact synthetic"):
        review_synthetic_context_reuse(
            state[0], state[1], state[2], state[3], object(),
            captured_at_ms=100, now_ms=100, max_age_ms=10,
        )
