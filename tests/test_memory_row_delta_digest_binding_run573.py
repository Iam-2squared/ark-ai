"""Retained Memory row-delta review SHA binds actual rows and full event tail.

All SQLite records and text are synthetic. A local SHA is not a writer
signature, consent, erasure confirmation or authorization to disclose.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3

import pytest

import ark.memory.sqlite_retained_row_delta_review as delta
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


def _seed_and_fork(tmp_path, content, clock_ms):
    origin = SQLiteMemoryStore(tmp_path / "origin.sqlite3", clock_ms=lambda: 1000)
    scope = MemoryScope("fixture-owner", "notes")
    origin.put(MemoryWrite(scope, "note", "original synthetic text"), expected_revision=0)
    retained = delta.capture_local_memory_row_delta(origin)
    reports = []
    instances = []
    for index, (new_text, at) in enumerate(zip(content, clock_ms, strict=True)):
        path = tmp_path / f"fork_{index}.sqlite3"
        with sqlite3.connect(origin.path) as source, sqlite3.connect(path) as target:
            source.backup(target)
        store = SQLiteMemoryStore(path, clock_ms=lambda tick=at: tick)
        store.put(MemoryWrite(scope, "note", new_text), expected_revision=1)
        report = delta.review_retained_memory_row_delta(store, retained)
        reports.append(report)
        instances.append(store)
    return retained, tuple(reports), tuple(instances)


@pytest.mark.parametrize(("contents", "timestamps"), (
    (("synthetic alpha", "synthetic beta"), (2000, 2000)),
    (("synthetic same", "synthetic same"), (2000, 2001)),
))
def test_sibling_tails_with_equal_counts_have_different_review_digest(
    tmp_path, contents, timestamps,
):
    retained, (left, right), _ = _seed_and_fork(tmp_path, contents, timestamps)
    assert retained.event_count == 1
    assert (
        left.retained_rows, left.current_rows,
        left.appended_events, left.explained_changes,
    ) == (1, 1, 1, 1)
    assert (
        left.retained_rows, left.current_rows,
        left.appended_events, left.explained_changes,
    ) == (
        right.retained_rows, right.current_rows,
        right.appended_events, right.explained_changes,
    )
    # The older count-only review digest could not distinguish these
    # two otherwise-valid row/event tails.
    legacy_payload = json.dumps(
        (
            (retained.event_count, retained.last_event_id, retained.event_prefix_sha256),
            1, 1, 2, 1,
        ), separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    assert hashlib.sha256(delta._DOMAIN + legacy_payload).hexdigest()
    assert left.review_sha256 != right.review_sha256
    assert left.writer_authenticated is right.writer_authenticated is False
    assert left.disclosure_authorized is right.disclosure_authorized is False
    assert left.action_authorized is right.action_authorized is False


def test_review_digest_is_recomputable_from_bounded_verified_witnesses(tmp_path):
    retained, (report,), (store,) = _seed_and_fork(
        tmp_path, ("synthetic update",), (2000,),
    )
    rows, events = delta._scan(store)
    old_rows = retained.rows
    epoch = (
        retained.event_count, retained.last_event_id,
        retained.event_prefix_sha256, retained.rows,
    )
    full_event_root = delta._prefix_hash(events, len(events))
    changed_ids = {entry[1] for entry in events[retained.event_count:]}
    encoded = json.dumps(
        (epoch, old_rows, rows, len(events) - retained.event_count,
         full_event_root, tuple(sorted(changed_ids)), report.explained_changes),
        separators=(",", ":"), ensure_ascii=True,
    ).encode("ascii")
    expected = hashlib.sha256(delta._REVIEW_DOMAIN + encoded).hexdigest()
    assert report.review_sha256 == expected
    assert "synthetic update" not in repr(report)
    assert "synthetic update" not in repr(retained)
