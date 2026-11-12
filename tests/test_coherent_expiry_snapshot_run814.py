"""Real SQLite snapshot semantics for content-free multi-scope expiry review."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.memory.coherent_expiry_snapshot_review as coherent
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.expiry_candidate_preview import review_memory_expiry_candidates


def _setup(tmp_path):
    path = tmp_path / "coherent-expiry.sqlite"
    store = SQLiteMemoryStore(path, clock_ms=lambda: 1000)
    notes = MemoryScope("same-owner", "notes")
    tasks = MemoryScope("same-owner", "tasks")
    foreign = MemoryScope("foreign-owner", "notes")
    store.put(MemoryWrite(notes, "first", "private-text-alpha", expires_at_ms=1200))
    store.put(MemoryWrite(tasks, "second", "private-text-beta", expires_at_ms=1300))
    store.put(MemoryWrite(foreign, "third", "foreign-content", expires_at_ms=1300))
    store.put(MemoryWrite(notes, "future", "keep-me", expires_at_ms=2500))
    return store, notes, tasks, foreign


def _review(store, notes, tasks, *, limit=100, now_ms=1500):
    return coherent.review_coherent_expiry_snapshot(
        store, (notes, tasks), now_ms=now_ms, limit=limit,
    )


def test_same_transaction_scopes_match_individual_quiescent_pages(tmp_path):
    store, notes, tasks, _ = _setup(tmp_path)
    report = _review(store, notes, tasks)
    assert report == _review(store, notes, tasks)
    expected = {
        item.scope_sha256: item
        for item in (
            review_memory_expiry_candidates(store, notes, now_ms=1500),
            review_memory_expiry_candidates(store, tasks, now_ms=1500),
        )
    }
    assert report.pages == tuple(expected[key] for key in sorted(expected))
    assert report.cohort.scope_hashes == tuple(sorted(expected))
    assert report.cohort.candidate_count == 2
    assert report.cohort.truncated_scopes == ()
    assert report.read_at_ms == 1500
    assert len(report.snapshot_sha256) == 64
    assert "private-text-alpha" not in repr(report)
    assert "foreign-content" not in repr(report)
    assert report.automatic_purge_authorized is False
    assert report.trusted_clock_verified is False
    assert report.owner_consent_authenticated is False
    assert report.independent_historical_custody_proven is False
    assert report.cross_store_atomicity_proven is False
    assert report.cohort.cross_scope_atomicity_proven is False


def test_limit_is_per_scope_and_overflow_explicit(tmp_path):
    store, notes, tasks, _ = _setup(tmp_path)
    store.put(MemoryWrite(notes, "extra", "private-overflow", expires_at_ms=1400))
    report = _review(store, notes, tasks, limit=1)
    assert report.cohort.candidate_count == 2
    assert len(report.cohort.truncated_scopes) == 1
    by_hash = {page.scope_sha256: page for page in report.pages}
    notes_hash = review_memory_expiry_candidates(
        store, notes, now_ms=1500, limit=1,
    ).scope_sha256
    assert by_hash[notes_hash].has_more is True
    assert by_hash[notes_hash].candidate_count == 1
    assert report.snapshot_sha256 != _review(store, notes, tasks).snapshot_sha256


def test_one_sqlite_wal_epoch_across_scopes(tmp_path, monkeypatch):
    store, notes, tasks, _ = _setup(tmp_path)
    writer = SQLiteMemoryStore(store.path, clock_ms=lambda: 1100)
    original_connect = coherent.SQLiteMemoryStore._connect_readonly
    reads = []
    changed = []

    def instrumented_connect(self):
        conn = original_connect(self)

        def after_first_page(sql):
            if sql.startswith("SELECT * FROM memories WHERE"):
                reads.append(sql)
                if len(reads) == 2:
                    # The first SELECT established the SQLite read snapshot.
                    writer.put(MemoryWrite(
                        tasks, "later", "private-new", expires_at_ms=1400,
                    ))
                    changed.append("committed")

        conn.set_trace_callback(after_first_page)
        return conn

    monkeypatch.setattr(
        coherent.SQLiteMemoryStore, "_connect_readonly", instrumented_connect,
    )
    old = _review(store, notes, tasks)
    assert changed == ["committed"]
    assert old.cohort.candidate_count == 2
    # A fresh transaction sees the committed additional due row.
    new = _review(store, notes, tasks)
    assert new.cohort.candidate_count == 3
    assert new.snapshot_sha256 != old.snapshot_sha256


@pytest.mark.parametrize(
    "bad",
    (
        "mixed-owner", "duplicate", "list", "empty", "bool-clock",
        "clock-overflow", "bad-limit", "bool-limit", "too-many",
        "scope-subclass", "store-subclass",
    ),
)
def test_invalid_scope_or_clock_refused_before_private_rows(tmp_path, bad):
    store, notes, tasks, foreign = _setup(tmp_path)
    args = {"store": store, "scopes": (notes, tasks), "now_ms": 1500, "limit": 10}
    if bad == "mixed-owner":
        args["scopes"] = (notes, foreign)
    elif bad == "duplicate":
        args["scopes"] = (notes, notes)
    elif bad == "list":
        args["scopes"] = [notes, tasks]
    elif bad == "empty":
        args["scopes"] = ()
    elif bad == "bool-clock":
        args["now_ms"] = True
    elif bad == "clock-overflow":
        args["now_ms"] = 1 << 63
    elif bad == "bad-limit":
        args["limit"] = 0
    elif bad == "bool-limit":
        args["limit"] = False
    elif bad == "too-many":
        args["scopes"] = tuple(
            MemoryScope("same-owner", f"namespace-{number}") for number in range(17)
        )
    elif bad == "scope-subclass":
        class FakeScope(MemoryScope):
            pass

        args["scopes"] = (FakeScope("same-owner", "notes"), tasks)
    elif bad == "store-subclass":
        class FakeStore(SQLiteMemoryStore):
            pass

        args["store"] = FakeStore(store.path, clock_ms=lambda: 1000)
    with pytest.raises(coherent.CoherentExpirySnapshotRejected):
        coherent.review_coherent_expiry_snapshot(**args)


@pytest.mark.parametrize("changed", ("helper", "result", "cohort"))
def test_original_verifiers_and_false_only_result_are_pinned(
    tmp_path, monkeypatch, changed,
):
    store, notes, tasks, _ = _setup(tmp_path)
    with monkeypatch.context() as patch:
        if changed == "helper":
            patch.setattr(
                coherent.preview_module, "_check_due_event_chain",
                lambda *args: (_ for _ in ()).throw(
                    AssertionError("substituted candidate verifier executed")
                ),
            )
        elif changed == "result":
            patch.setattr(
                coherent.CoherentExpirySnapshot, "automatic_purge_authorized",
                property(lambda _: True),
            )
        else:
            patch.setattr(
                coherent.cohort_module, "aggregate_memory_expiry_cohort",
                lambda **kwargs: (_ for _ in ()).throw(
                    AssertionError("substituted cohort verifier executed")
                ),
            )
        with pytest.raises(
            coherent.CoherentExpirySnapshotRejected, match="protocol changed",
        ):
            _review(store, notes, tasks)


def test_reject_modified_event_history(tmp_path):
    store, notes, tasks, _ = _setup(tmp_path)
    with store._connect() as conn:
        conn.execute(
            "UPDATE memory_events SET revision=17 "
            "WHERE memory_id=(SELECT memory_id FROM memories "
            "WHERE namespace='notes' AND source_id='first')"
        )
    with pytest.raises(coherent.preview_module.MemoryExpiryPreviewRejected):
        _review(store, notes, tasks)


def test_scope_mutation_during_connection_rejected(tmp_path, monkeypatch):
    store, notes, tasks, _ = _setup(tmp_path)
    original_connect = coherent.SQLiteMemoryStore._connect_readonly

    def mutate_then_open(self):
        conn = original_connect(self)
        object.__setattr__(notes, "namespace", "altered")
        return conn

    monkeypatch.setattr(
        coherent.SQLiteMemoryStore, "_connect_readonly", mutate_then_open,
    )
    with pytest.raises(
        coherent.CoherentExpirySnapshotRejected, match="source changed",
    ):
        _review(store, notes, tasks)
