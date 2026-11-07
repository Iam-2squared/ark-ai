"""Detached SQLite synthetic READ digest journal regressions."""

from __future__ import annotations

import hashlib
import multiprocessing as mp
import sqlite3
from pathlib import Path

import pytest

from ark.agency.disconnected_read_journal import (
    DisconnectedReadJournal,
    ReadJournalRejected,
    ReadJournalWitness,
    ReadReceipt,
    genesis_witness,
)

REQUEST = "req_" + "a" * 32
SHA = "b" * 64


def receipt(step: int = 1, request: str = REQUEST) -> ReadReceipt:
    return ReadReceipt(request, "step_" + f"{step:016x}", "math.sum", SHA, "c" * 64)


def new_db(tmp_path: Path) -> Path:
    return tmp_path / "only-synthetic-read-journal.sqlite"


def test_create_empty_and_no_dispatch(tmp_path):
    path = new_db(tmp_path)
    assert not path.exists()
    with DisconnectedReadJournal.create(path) as journal:
        assert journal.verify(genesis_witness()) == genesis_witness()
        state = journal.append(receipt(), genesis_witness())
        assert state.count == 1
        assert len(state.tip_sha256) == 64
        assert not state.dispatch_authorized
        assert not state.effect_proven
        assert not state.replay_authorized
        assert not state.independent_custody_proven
    with DisconnectedReadJournal.open(path) as reopened:
        assert reopened.verify(state) == state


def test_independent_witness_detects_truncation_after_restart(tmp_path):
    path = new_db(tmp_path)
    with DisconnectedReadJournal.create(path) as journal:
        first = journal.append(receipt(1), genesis_witness())
        second = journal.append(receipt(2), first)
    with sqlite3.connect(path) as connection:
        connection.execute("DELETE FROM receipts WHERE seq=2")
    with DisconnectedReadJournal.open(path) as reopened:
        assert reopened.verify(first) == first
        with pytest.raises(ReadJournalRejected, match="external witness"):
            reopened.verify(second)


def test_reject_deleted_interior_row(tmp_path):
    path = new_db(tmp_path)
    with DisconnectedReadJournal.create(path) as journal:
        state = genesis_witness()
        for n in range(1, 4):
            state = journal.append(receipt(n), state)
    with sqlite3.connect(path) as connection:
        connection.execute("DELETE FROM receipts WHERE seq=2")
    with pytest.raises(ReadJournalRejected, match="missing"):
        DisconnectedReadJournal.open(path)


@pytest.mark.parametrize("column", ["input_digest", "result_digest", "previous_sha", "chain_sha"])
def test_reject_mutated_row_fields(tmp_path, column):
    path = new_db(tmp_path)
    with DisconnectedReadJournal.create(path) as journal:
        journal.append(receipt(), genesis_witness())
    with sqlite3.connect(path) as connection:
        connection.execute(f"UPDATE receipts SET {column}=? WHERE seq=1", ("d" * 64,))
    with pytest.raises(ReadJournalRejected):
        DisconnectedReadJournal.open(path)


def test_duplicate_and_cas_stale_are_atomic(tmp_path):
    path = new_db(tmp_path)
    with DisconnectedReadJournal.create(path) as journal:
        first = journal.append(receipt(1), genesis_witness())
        with pytest.raises(ReadJournalRejected, match="stale"):
            journal.append(receipt(2), genesis_witness())
        with pytest.raises(ReadJournalRejected, match="duplicate"):
            journal.append(receipt(1), first)
        assert journal.verify(first) == first


@pytest.mark.parametrize("field,value", [
    ("request_id", "req_invalid"), ("step_id", "step_wrong"),
    ("operation", "os.exec"), ("input_digest", "X" * 64),
    ("result_digest", "a" * 65), ("operation", True),
])
def test_invalid_receipt_no_new_row(tmp_path, field, value):
    path = new_db(tmp_path)
    with DisconnectedReadJournal.create(path) as journal:
        raw = dict(request_id=REQUEST, step_id="step_" + "1" * 16,
                   operation="math.sum", input_digest=SHA, result_digest="c" * 64)
        raw[field] = value
        with pytest.raises(ReadJournalRejected):
            journal.append(ReadReceipt(**raw), genesis_witness())
        journal.verify(genesis_witness())


@pytest.mark.parametrize("state", [
    ReadJournalWitness(True, "b" * 64),
    ReadJournalWitness(-1, "b" * 64),
    ReadJournalWitness(129, "b" * 64),
    ReadJournalWitness(0, "invalid"),
])
def test_invalid_external_witness(tmp_path, state):
    with DisconnectedReadJournal.create(new_db(tmp_path)) as journal:
        with pytest.raises(ReadJournalRejected):
            journal.verify(state)


def test_never_overwrite_existing_file(tmp_path):
    path = new_db(tmp_path)
    path.write_text("do not replace")
    with pytest.raises(ReadJournalRejected):
        DisconnectedReadJournal.create(path)
    assert path.read_text() == "do not replace"


def test_foreign_schema_rejected(tmp_path):
    path = new_db(tmp_path)
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE unrelated (id INTEGER)")
    with pytest.raises(ReadJournalRejected):
        DisconnectedReadJournal.open(path)
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT name FROM sqlite_master").fetchall() == [
            ("unrelated",),
        ]


def test_symlink_target_rejected(tmp_path):
    target = tmp_path / "existing.db"
    target.write_text("immutable")
    link = new_db(tmp_path)
    try:
        link.symlink_to(target)
    except OSError:
        pytest.skip("symlink creation not allowed")
    with pytest.raises(ReadJournalRejected):
        DisconnectedReadJournal.create(link)
    with pytest.raises(ReadJournalRejected):
        DisconnectedReadJournal.open(link)
    assert target.read_text() == "immutable"


def _competing_append(path: str, answer: mp.Queue) -> None:
    try:
        with DisconnectedReadJournal.open(Path(path)) as journal:
            result = journal.append(receipt(1), genesis_witness())
        answer.put(("ok", result.tip_sha256))
    except ReadJournalRejected:
        answer.put(("blocked", None))


def test_cross_process_one_winner(tmp_path):
    path = new_db(tmp_path)
    with DisconnectedReadJournal.create(path):
        pass
    context = mp.get_context("spawn")
    queue = context.Queue()
    workers = [context.Process(target=_competing_append, args=(str(path), queue))
               for _ in range(2)]
    for worker in workers:
        worker.start()
    responses = [queue.get(timeout=20) for _ in workers]
    for worker in workers:
        worker.join(timeout=20)
        assert worker.exitcode == 0
    assert sorted(item[0] for item in responses) == ["blocked", "ok"]
    winner = next(tip for label, tip in responses if label == "ok")
    with DisconnectedReadJournal.open(path) as journal:
        assert journal.verify(ReadJournalWitness(1, winner)).tip_sha256 == winner


def test_deterministic_digest_across_new_databases(tmp_path):
    values = []
    for i in (1, 2):
        with DisconnectedReadJournal.create(tmp_path / f"synthetic-{i}.db") as journal:
            values.append(journal.append(receipt(), genesis_witness()).tip_sha256)
    assert values[0] == values[1]
    assert values[0] != hashlib.sha256(SHA.encode()).hexdigest()


def test_reject_unexpected_trigger_and_table(tmp_path):
    path = new_db(tmp_path)
    with DisconnectedReadJournal.create(path):
        pass
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE extra (value TEXT)")
        connection.execute(
            "CREATE TRIGGER dangerous AFTER INSERT ON receipts "
            "BEGIN INSERT INTO extra VALUES ('unwanted'); END"
        )
    with pytest.raises(ReadJournalRejected, match="schema changed"):
        DisconnectedReadJournal.open(path)
    with sqlite3.connect(path) as connection:
        assert connection.execute("SELECT * FROM extra").fetchall() == []
