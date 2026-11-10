"""Two spawned interpreters race an inert proactive SQLite preparation.

Only content-minimized fixture markers may be stored. Successful preparation
never authorizes a notification, dispatcher, real scheduler or tool execution.
"""

from __future__ import annotations

from multiprocessing import get_context
from pathlib import Path
from queue import Empty

import pytest

from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _policy():
    return SyntheticTriggerPolicy(
        "synthetic-owner", "private", "synthetic-definition",
        1, "pinned-policy", 5, 1000, 8,
    )


def _prepare_in_child(path, observation, released, messages):
    try:
        ledger = SyntheticProactiveLedger(Path(path))
        messages.put(("ready", observation, None))
        if not released.wait(30):
            raise RuntimeError("proactive test release timed out")
        try:
            receipt = ledger.prepare(
                _policy(),
                source_digest="a" * 64,
                observation_digest=observation,
                observed_at_ms=90, now_ms=100,
            )
        except SyntheticTriggerRejected as exc:
            messages.put(("rejected", observation, str(exc)))
        else:
            assert receipt.notification_authorized is False
            assert receipt.dispatch_authorized is False
            assert receipt.automatic_replay_authorized is False
            messages.put(("prepared", observation, receipt.trigger_id))
    except Exception as exc:
        messages.put(("error", observation, repr(exc)))


@pytest.mark.parametrize("same_observation", (True, False))
def test_proactive_concurrent_interval_fences_are_process_durable(
    tmp_path, same_observation,
):
    path = tmp_path / "synthetic-proactive-race.sqlite3"
    ledger = SyntheticProactiveLedger(path)
    context = get_context("spawn")
    released = context.Event()
    messages = context.Queue()
    observations = ("b" * 64, "b" * 64 if same_observation else "c" * 64)
    children = [
        context.Process(
            target=_prepare_in_child,
            args=(str(path), observation, released, messages),
        )
        for observation in observations
    ]
    try:
        for child in children:
            child.start()
        prepared = [messages.get(timeout=35) for _ in children]
        assert all(entry[0] == "ready" for entry in prepared), prepared
        released.set()
        outcomes = [messages.get(timeout=35) for _ in children]
    except Empty as exc:
        pytest.fail(f"spawned proactive preparation did not respond: {exc}")
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
    assert sorted(outcome[0] for outcome in outcomes) == ["prepared", "rejected"]
    assert "minimum preparation interval" in next(
        outcome[2] for outcome in outcomes if outcome[0] == "rejected"
    )
    assert ledger.count() == 1
    assert SyntheticProactiveLedger(path).count() == 1
