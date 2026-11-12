"""Read-only occurrence frontier regression: no dispatch, no retry, no leaks."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)
from ark.agency import disconnected_occurrence_frontier_review as frontier


def _store(tmp_path: Path, *, name: str = "synthetic.db") -> SyntheticOccurrenceStore:
    return SyntheticOccurrenceStore(tmp_path / name)


def _add(
    store: SyntheticOccurrenceStore,
    token: str,
    *,
    bound: str = "c",
    at: int = 10,
    expiry: int = 100,
) -> None:
    with sqlite3.connect(store._path) as conn:
        conn.execute(
            "INSERT INTO synthetic_occurrence_reservations VALUES (?,?,?,?,?,?,?)",
            (
                token * 64,
                "occ_" + "a" * 64,
                "tools_" + "b" * 64,
                "bound_" + bound * 64,
                "act_" + "d" * 64,
                at,
                expiry,
            ),
        )


def _second(store: SyntheticOccurrenceStore, *, token: str = "e") -> None:
    with sqlite3.connect(store._path) as conn:
        conn.execute(
            "INSERT INTO synthetic_occurrence_reservations VALUES (?,?,?,?,?,?,?)",
            (
                token * 64, "occ_" + "f" * 64,
                "tools_" + "b" * 64, "bound_" + "c" * 64,
                "act_" + "d" * 64, 11, 100,
            ),
        )


def test_empty_commitment_is_inert_and_stable(tmp_path: Path) -> None:
    store = _store(tmp_path)
    actual = frontier.review_synthetic_occurrence_frontier(store)
    assert actual.row_count == 0
    assert actual.latest_reserved_at_ms == -1
    assert len(actual.commitment_sha256) == 64
    assert frontier.review_synthetic_occurrence_frontier(
        store, retained=actual,
    ) == actual
    assert actual.dispatch_authorized is False
    assert actual.automatic_replay_authorized is False
    assert actual.human_approval_authenticated is False
    assert actual.external_outcome_proven is False


def test_one_row_coherent_snapshot_does_not_expose_token(tmp_path: Path) -> None:
    store = _store(tmp_path)
    _add(store, "1", at=0)
    actual = frontier.review_synthetic_occurrence_frontier(store)
    assert actual.row_count == 1
    assert actual.latest_reserved_at_ms == 0
    assert "1" * 64 not in repr(actual)
    assert frontier.review_synthetic_occurrence_frontier(
        store, retained=actual,
    ) == actual


def test_canonical_set_order_is_insertion_independent(tmp_path: Path) -> None:
    first = _store(tmp_path, name="first.db")
    _add(first, "1")
    _second(first)
    other = _store(tmp_path, name="other.db")
    _second(other)
    _add(other, "1")
    assert (
        frontier.review_synthetic_occurrence_frontier(first)
        == frontier.review_synthetic_occurrence_frontier(other)
    )


@pytest.mark.parametrize("change", ["valid_rewrite", "append", "delete"])
def test_retained_frontier_rejects_same_count_and_lifecycle_drift(
    tmp_path: Path, change: str,
) -> None:
    store = _store(tmp_path)
    _add(store, "1")
    previous = frontier.review_synthetic_occurrence_frontier(store)
    if change == "valid_rewrite":
        with sqlite3.connect(store._path) as conn:
            conn.execute(
                "UPDATE synthetic_occurrence_reservations "
                "SET bound_action_id=?",
                ("bound_" + "e" * 64,),
            )
    elif change == "append":
        _second(store)
    else:
        with sqlite3.connect(store._path) as conn:
            conn.execute("DELETE FROM synthetic_occurrence_reservations")
    assert frontier.review_synthetic_occurrence_frontier(store) != previous
    with pytest.raises(SyntheticReplayRejected, match="retained.*differs"):
        frontier.review_synthetic_occurrence_frontier(
            store, retained=previous,
        )


@pytest.mark.parametrize(
    "retained",
    [
        object(),
        frontier.SyntheticOccurrenceFrontier(True, "a" * 64, 2),
        frontier.SyntheticOccurrenceFrontier(1, "a" * 64, -1),
        frontier.SyntheticOccurrenceFrontier(0, "a" * 64, 0),
        frontier.SyntheticOccurrenceFrontier(1, "x" * 64, 3),
        frontier.SyntheticOccurrenceFrontier(10_001, "a" * 64, 3),
    ],
)
def test_forged_retained_shape_denied_before_sqlite(
    tmp_path: Path, retained: object,
) -> None:
    missing = tmp_path / "missing.db"
    store = object.__new__(SyntheticOccurrenceStore)
    store._path = missing
    with pytest.raises(SyntheticReplayRejected, match="retained|type"):
        frontier.review_synthetic_occurrence_frontier(store, retained=retained)
    assert not missing.exists()


def test_read_only_missing_source_does_not_create(tmp_path: Path) -> None:
    store = _store(tmp_path)
    store._path.unlink()
    with pytest.raises((SyntheticReplayRejected, sqlite3.OperationalError)):
        frontier.review_synthetic_occurrence_frontier(store)
    assert not store._path.exists()


def test_nonexact_store_subclass_denied(tmp_path: Path) -> None:
    class Fake(SyntheticOccurrenceStore):
        pass

    fake = object.__new__(Fake)
    fake._path = tmp_path / "nonexistent.db"
    with pytest.raises(SyntheticReplayRejected, match="exact"):
        frontier.review_synthetic_occurrence_frontier(fake)


def test_swapped_result_slot_refused_before_getter(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = _store(tmp_path)
    seen: list[str] = []

    def bad(_self: object) -> int:
        seen.append("executed")
        return 0

    monkeypatch.setattr(
        frontier.SyntheticOccurrenceFrontier, "row_count", property(bad),
    )
    with pytest.raises(SyntheticReplayRejected, match="contract"):
        frontier.review_synthetic_occurrence_frontier(store)
    assert not seen


def test_swapped_digest_callback_denied_before_db(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    store = _store(tmp_path)
    store._path.unlink()
    original = frontier.hashlib.sha256
    monkeypatch.setattr(frontier.hashlib, "sha256", lambda *_: original(b"x"))
    with pytest.raises(SyntheticReplayRejected, match="contract"):
        frontier.review_synthetic_occurrence_frontier(store)
    assert not store._path.exists()
