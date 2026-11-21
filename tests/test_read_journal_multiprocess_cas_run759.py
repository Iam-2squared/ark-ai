"""Process-isolated CAS race for the disconnected, digest-only READ journal.

Only one append can spend a retained journal tip; its recovered receipt must
match the durable winner. No READ tool executed, and no replay/dispatch consent
is granted by a synthetic witness.
"""

from __future__ import annotations

from multiprocessing import get_context
from pathlib import Path
from queue import Empty

import pytest

from ark.agency.disconnected_read_journal import (
    DisconnectedReadJournal,
    ReadJournalRejected,
    ReadReceipt,
    genesis_witness,
)


def _receipt(number: int) -> ReadReceipt:
    return ReadReceipt(
        "req_" + "a" * 32,
        "step_" + f"{number:016x}",
        "math.sum",
        "b" * 64,
        "c" * 64,
    )


def _compete(path, retained, step_number, released, queue):
    try:
        with DisconnectedReadJournal.open(Path(path)) as journal:
            queue.put(("ready", step_number, None))
            if not released.wait(30):
                raise RuntimeError("synthetic READ journal race timed out")
            try:
                tip = journal.append(_receipt(step_number), retained)
            except ReadJournalRejected as exc:
                queue.put(("rejected", step_number, str(exc)))
            else:
                assert tip.dispatch_authorized is False
                assert tip.replay_authorized is False
                assert tip.effect_proven is False
                queue.put(("committed", step_number, tip))
    except Exception as exc:
        queue.put(("error", step_number, repr(exc)))


@pytest.mark.parametrize("same_receipt", (True, False))
def test_spawned_read_journal_append_has_one_retained_tip_winner(
    tmp_path, same_receipt,
):
    path = tmp_path / "read-journal-contention.sqlite3"
    with DisconnectedReadJournal.create(path) as seed:
        retained = seed.append(_receipt(1), genesis_witness())

    numbers = (2, 2 if same_receipt else 3)
    context = get_context("spawn")
    released = context.Event()
    messages = context.Queue()
    children = [
        context.Process(
            target=_compete,
            args=(str(path), retained, number, released, messages),
        )
        for number in numbers
    ]
    try:
        for child in children:
            child.start()
        ready = [messages.get(timeout=35) for _ in children]
        assert [item[0] for item in ready] == ["ready", "ready"], ready
        released.set()
        outcomes = [messages.get(timeout=35) for _ in children]
    except Empty as exc:
        pytest.fail(f"spawned READ journal CAS worker hung: {exc}")
    finally:
        released.set()
        for child in children:
            child.join(timeout=20)
            if child.is_alive():
                child.terminate()
                child.join(timeout=5)
        messages.close()
        messages.join_thread()

    assert all(child.exitcode == 0 for child in children)
    assert sorted(item[0] for item in outcomes) == ["committed", "rejected"], outcomes
    winner = next(item for item in outcomes if item[0] == "committed")
    rejection = next(item for item in outcomes if item[0] == "rejected")
    assert "stale or exhausted journal witness" in rejection[2]
    with DisconnectedReadJournal.open(path) as cold:
        with pytest.raises(ReadJournalRejected, match="external witness"):
            cold.verify(retained)
        snapshot = cold.recover_receipts(winner[2])
        assert snapshot.witness == winner[2]
        assert snapshot.receipts == (_receipt(1), _receipt(winner[1]))
        assert snapshot.dispatch_authorized is False
        assert snapshot.effect_proven is False
        assert snapshot.automatic_replay_authorized is False
        assert snapshot.independent_custody_proven is False
