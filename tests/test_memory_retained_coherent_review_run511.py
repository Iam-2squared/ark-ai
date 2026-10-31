"""A single local read snapshot must bind historic events and current rows."""

import hashlib
import sqlite3
from dataclasses import replace

import pytest

import ark.memory.sqlite_retained_coherent_review as coherent
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_event_alignment import review_memory_event_alignment
from ark.memory.sqlite_event_prefix_review import capture_local_memory_event_prefix


def _store(tmp_path):
    return SQLiteMemoryStore(tmp_path / "coherent.db", clock_ms=lambda: 5000)


def _write(scope, key="first", content="private content"):
    return MemoryWrite(scope, key, content)


def _witnesses(store):
    return capture_local_memory_event_prefix(store), review_memory_event_alignment(store)


def test_empty_genesis_is_a_content_free_denial_only_snapshot(tmp_path):
    store = _store(tmp_path)
    before = _witnesses(store)
    review = coherent.review_retained_coherent_memory(store, *before)
    assert (review.previous_event_count, review.current_event_count) == (0, 0)
    assert (review.row_count, review.scope_count, review.last_event_id) == (0, 0, 0)
    assert review.status == "UNCHANGED_LOCAL_HISTORY"
    assert len(review.review_sha256) == 64
    assert review.independently_authenticated is False
    assert review.historical_writer_authenticated is False
    assert review.consent_verified is False
    assert review.memory_disclosure_authorized is False
    assert review.action_authorized is False
    assert review.cross_store_atomicity_proven is False


def test_current_single_transaction_hashes_match_existing_separate_algorithms(tmp_path):
    store = _store(tmp_path)
    scope = MemoryScope("owner", "notes")
    store.put(_write(scope))
    prefix, alignment = _witnesses(store)
    result = coherent.review_retained_coherent_memory(store, prefix, alignment)
    assert result.current_alignment_sha256 == alignment.digest
    assert result.current_event_sha256 == prefix.prefix_sha256
    assert result.status == "UNCHANGED_LOCAL_HISTORY"
    assert "private content" not in repr(result)


def test_append_is_not_claimed_as_authenticated_history(tmp_path):
    store = _store(tmp_path)
    scope = MemoryScope("owner")
    store.put(_write(scope))
    retained = _witnesses(store)
    store.put(_write(scope, "second"))
    result = coherent.review_retained_coherent_memory(store, *retained)
    assert (result.previous_event_count, result.current_event_count) == (1, 2)
    assert (result.row_count, result.last_event_id) == (2, 2)
    assert result.status == "ADVANCED_PREFIX_UNAUTHENTICATED"
    assert result.action_authorized is False


def test_delete_then_recreate_tracks_a_coherent_new_lifecycle(tmp_path):
    store = _store(tmp_path)
    scope = MemoryScope("owner")
    initial = store.put(_write(scope))
    retained = _witnesses(store)
    assert store.delete(initial.memory_id, scope, expected_revision=1)
    store.put(_write(scope, content="different"))
    result = coherent.review_retained_coherent_memory(store, *retained)
    assert (result.current_event_count, result.row_count) == (3, 1)


def test_multiple_owner_and_namespace_histories_are_scanned_together(tmp_path):
    store = _store(tmp_path)
    for owner, namespace in (
        ("owner-a", "one"), ("owner-a", "two"), ("owner-b", "one"),
    ):
        store.put(_write(MemoryScope(owner, namespace), owner + namespace))
    prefix, alignment = _witnesses(store)
    result = coherent.review_retained_coherent_memory(store, prefix, alignment)
    assert (result.scope_count, result.row_count, result.current_event_count) == (3, 3, 3)


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("occurred_at_ms", 7000),
        ("revision", 2),
        ("owner_id", "other"),
    ],
)
def test_historic_prefix_rewrite_cannot_hide_behind_an_append(
    tmp_path, column, value,
):
    store = _store(tmp_path)
    scope = MemoryScope("owner")
    store.put(_write(scope))
    retained = _witnesses(store)
    store.put(_write(scope, "second"))
    with sqlite3.connect(store.path) as conn:
        conn.execute(f"UPDATE memory_events SET {column}=? WHERE event_id=1", (value,))
    with pytest.raises(coherent.MemoryCoherentHistoryRejected):
        coherent.review_retained_coherent_memory(store, *retained)


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("updated_at_ms", 7000),
        ("expires_at_ms", 9000),
        ("metadata_json", '{"tag":"silent"}'),
    ],
)
def test_silent_live_row_drift_without_event_is_rejected(tmp_path, column, value):
    store = _store(tmp_path)
    store.put(_write(MemoryScope("owner")))
    retained = _witnesses(store)
    with sqlite3.connect(store.path) as conn:
        conn.execute(f"UPDATE memories SET {column}=?", (value,))
    with pytest.raises(coherent.MemoryCoherentHistoryRejected):
        coherent.review_retained_coherent_memory(store, *retained)


def test_stored_row_content_integrity_must_still_be_valid(tmp_path):
    store = _store(tmp_path)
    store.put(_write(MemoryScope("owner")))
    retained = _witnesses(store)
    with sqlite3.connect(store.path) as conn:
        conn.execute("UPDATE memories SET content='changed without checksum'")
    with pytest.raises(coherent.MemoryCoherentHistoryRejected):
        coherent.review_retained_coherent_memory(store, *retained)


def test_lost_create_event_is_rejected_even_if_rows_still_exist(tmp_path):
    store = _store(tmp_path)
    store.put(_write(MemoryScope("owner")))
    retained = _witnesses(store)
    with sqlite3.connect(store.path) as conn:
        conn.execute("DELETE FROM memory_events")
    with pytest.raises(coherent.MemoryCoherentHistoryRejected):
        coherent.review_retained_coherent_memory(store, *retained)


@pytest.mark.parametrize(
    "field", ["event_count", "last_event_id"],
)
def test_retained_witnesses_from_different_epochs_are_rejected(tmp_path, field):
    store = _store(tmp_path)
    store.put(_write(MemoryScope("owner")))
    prefix, alignment = _witnesses(store)
    altered = replace(alignment, **{field: getattr(alignment, field) + 1})
    # Either a malformed retained shape or a cross-witness mismatch must
    # fail closed; do not constrain the denial to a particular diagnostic.
    with pytest.raises(coherent.MemoryCoherentHistoryRejected):
        coherent.review_retained_coherent_memory(store, prefix, altered)


def test_no_effect_on_rows_events_or_metadata(tmp_path):
    store = _store(tmp_path)
    store.put(_write(MemoryScope("owner")))
    retained = _witnesses(store)
    with sqlite3.connect(store.path) as conn:
        before = tuple(conn.iterdump())
    coherent.review_retained_coherent_memory(store, *retained)
    with sqlite3.connect(store.path) as conn:
        assert tuple(conn.iterdump()) == before


def test_result_repeated_on_unchanged_wal_is_deterministic(tmp_path):
    store = _store(tmp_path)
    store.put(_write(MemoryScope("owner")))
    retained = _witnesses(store)
    one = coherent.review_retained_coherent_memory(store, *retained)
    two = coherent.review_retained_coherent_memory(store, *retained)
    assert one == two
    assert hashlib.sha256(one.review_sha256.encode()).digest()


def test_inflight_wal_append_cannot_mix_row_and_event_epochs(tmp_path, monkeypatch):
    store = _store(tmp_path)
    scope = MemoryScope("owner")
    store.put(_write(scope))
    retained = _witnesses(store)
    real_record = coherent._record
    injected = False

    def append_after_first_row(row):
        nonlocal injected
        result = real_record(row)
        if not injected:
            injected = True
            store.put(_write(scope, "second"))
        return result

    monkeypatch.setattr(coherent, "_record", append_after_first_row)
    result = coherent.review_retained_coherent_memory(store, *retained)
    assert injected is True
    assert (result.row_count, result.current_event_count) == (1, 1)
    assert result.status == "UNCHANGED_LOCAL_HISTORY"
    new_result = coherent.review_retained_coherent_memory(store, *retained)
    assert new_result.status == "ADVANCED_PREFIX_UNAUTHENTICATED"
    assert (new_result.row_count, new_result.current_event_count) == (2, 2)


def test_retained_witness_retargeted_during_scan_is_rejected(tmp_path, monkeypatch):
    store = _store(tmp_path)
    store.put(_write(MemoryScope("owner")))
    prefix, alignment = _witnesses(store)
    original = coherent._record

    def mutate_original(row):
        result = original(row)
        object.__setattr__(prefix, "prefix_sha256", "0" * 64)
        return result

    monkeypatch.setattr(coherent, "_record", mutate_original)
    with pytest.raises(coherent.MemoryCoherentHistoryRejected, match="witness"):
        coherent.review_retained_coherent_memory(store, prefix, alignment)


def test_store_source_retargeted_during_scan_is_rejected(tmp_path, monkeypatch):
    store = _store(tmp_path)
    store.put(_write(MemoryScope("owner")))
    retained = _witnesses(store)
    original = coherent._record

    def retarget_store(row):
        record = original(row)
        store.path = tmp_path / "other.db"
        return record

    monkeypatch.setattr(coherent, "_record", retarget_store)
    with pytest.raises(coherent.MemoryCoherentHistoryRejected, match="source"):
        coherent.review_retained_coherent_memory(store, *retained)


def test_result_authority_monkeypatch_is_rejected(tmp_path, monkeypatch):
    store = _store(tmp_path)
    store.put(_write(MemoryScope("owner")))
    retained = _witnesses(store)
    monkeypatch.setattr(
        coherent.RetainedCoherentMemoryReview,
        "action_authorized",
        property(lambda self: True),
    )
    with pytest.raises(coherent.MemoryCoherentHistoryRejected, match="authority"):
        coherent.review_retained_coherent_memory(store, *retained)


def test_exact_types_required_for_each_source(tmp_path):
    store = _store(tmp_path)
    retained = _witnesses(store)
    with pytest.raises(coherent.MemoryCoherentHistoryRejected):
        coherent.review_retained_coherent_memory(object(), *retained)
    with pytest.raises(coherent.MemoryCoherentHistoryRejected):
        coherent.review_retained_coherent_memory(store, object(), retained[1])
    with pytest.raises(coherent.MemoryCoherentHistoryRejected):
        coherent.review_retained_coherent_memory(store, retained[0], object())


def test_bounded_scan_fails_closed(tmp_path, monkeypatch):
    store = _store(tmp_path)
    store.put(_write(MemoryScope("owner")))
    retained = _witnesses(store)
    monkeypatch.setattr(coherent, "_MAX_ROWS", 0)
    with pytest.raises(coherent.MemoryCoherentHistoryRejected, match="budget"):
        coherent.review_retained_coherent_memory(store, *retained)
