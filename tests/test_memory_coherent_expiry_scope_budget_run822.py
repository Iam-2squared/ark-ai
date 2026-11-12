"""Bounded content-free expiry ingress: reject private scope before DB access."""

from __future__ import annotations

import pytest

import ark.memory.coherent_expiry_snapshot_review as review
from ark.memory import MemoryScope, SQLiteMemoryStore


def _store(tmp_path):
    return SQLiteMemoryStore(tmp_path / "scope-budget.sqlite", clock_ms=lambda: 10)


@pytest.mark.parametrize(("owner", "namespace"), (
    ("a" * 257, "notes"),
    ("owner", "n" * 257),
    ("界" * 86, "notes"),
    ("owner", "界" * 86),
    ("bad\ud800", "notes"),
    ("owner", "bad\ud800"),
))
def test_unbounded_or_invalid_utf8_scopes_rejected_before_connection(
    tmp_path, monkeypatch: pytest.MonkeyPatch, owner: str, namespace: str,
) -> None:
    store = _store(tmp_path)
    calls: list[bool] = []

    def fail_if_opened(self):
        calls.append(True)
        raise AssertionError("private SQLite opened before bounded scope validation")

    monkeypatch.setattr(SQLiteMemoryStore, "_connect_readonly", fail_if_opened)
    with pytest.raises(review.CoherentExpirySnapshotRejected):
        review.review_coherent_expiry_snapshot(
            store, (MemoryScope(owner, namespace),), now_ms=50,
        )
    assert calls == []


@pytest.mark.parametrize("field", ("owner_id", "namespace"))
def test_reflected_wrong_type_refused_before_connection(
    tmp_path, monkeypatch: pytest.MonkeyPatch, field: str,
) -> None:
    store = _store(tmp_path)
    scope = MemoryScope("owner", "notes")
    object.__setattr__(scope, field, 24)
    calls = []
    monkeypatch.setattr(
        SQLiteMemoryStore, "_connect_readonly",
        lambda self: calls.append(True),
    )
    with pytest.raises(review.CoherentExpirySnapshotRejected):
        review.review_coherent_expiry_snapshot(store, (scope,), now_ms=50)
    assert calls == []


def test_exact_256_byte_scopes_yield_only_non_authorizing_empty_preview(tmp_path) -> None:
    store = _store(tmp_path)
    scope = MemoryScope("a" * 256, "b" * 256)
    result = review.review_coherent_expiry_snapshot(
        store, (scope,), now_ms=50,
    )
    assert result.cohort.candidate_count == 0
    assert len(result.pages) == 1
    assert result.pages[0].candidate_count == 0
    assert result.automatic_purge_authorized is False
    assert result.owner_consent_authenticated is False
    assert result.trusted_clock_verified is False
    assert result.cross_store_atomicity_proven is False


def test_ingress_budget_mutation_refused_by_protocol(
    tmp_path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = _store(tmp_path)
    monkeypatch.setattr(review, "_MAX_SCOPE_BYTES", 1)
    with pytest.raises(
        review.CoherentExpirySnapshotRejected, match="protocol changed",
    ):
        review.review_coherent_expiry_snapshot(
            store, (MemoryScope("owner", "notes"),), now_ms=50,
        )
