"""Actual OS process exits after a synthetic occurrence reservation COMMIT.

A lost synthetic receipt cannot permit reuse of its token or occurrence.
The local fixture does NOT authenticate consent or prove external effects.
"""

from __future__ import annotations

import hashlib
import os
from multiprocessing import get_context
from pathlib import Path

import pytest

from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import (
    SyntheticOccurrenceStore,
    SyntheticReplayRejected,
)
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NeverExecute:
    def execute(self, call: ToolCall) -> object:
        raise AssertionError("a synthetic reservation cannot execute a backend")


def _inputs():
    call = ToolCall("fixture.write", "offline.write", "local:private", {"test": 1})
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.write", "offline.write", Effect.WRITE, "mock-v1", _NeverExecute(),
        ),
    ))
    return registry, call


def _occurrence(name: str) -> str:
    return "occ_" + hashlib.sha256(name.encode()).hexdigest()


def _reserve_and_exit(path: str) -> None:
    registry, call = _inputs()
    token = OneShotAuthorization("private-token-must-not-persist", call.request_id, 200)
    receipt = SyntheticOccurrenceStore(Path(path)).reserve_synthetic(
        registry, call, token, occurrence_id=_occurrence("first"), now_ms=100,
    )
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.outcome_known is False
    os._exit(0)  # COMMIT, but no result ever reaches the original caller.


@pytest.mark.parametrize("collision", ("old_token", "old_occurrence"))
def test_cold_occurrence_reservation_lost_receipt_denies_replay(
    tmp_path: Path, collision,
):
    path = tmp_path / "synthetic-occurrence-lost-response.sqlite3"
    SyntheticOccurrenceStore(path)
    child = get_context("spawn").Process(
        target=_reserve_and_exit, args=(str(path),),
    )
    child.start()
    child.join(timeout=35)
    if child.is_alive():
        child.terminate()
        child.join(timeout=5)
    assert child.exitcode == 0

    registry, call = _inputs()
    cold = SyntheticOccurrenceStore(path)
    assert cold.count_synthetic() == 1
    token_id = (
        "private-token-must-not-persist"
        if collision == "old_token" else "separate-not-consent"
    )
    occurrence = (
        _occurrence("second")
        if collision == "old_token" else _occurrence("first")
    )
    with pytest.raises(SyntheticReplayRejected, match="already reserved"):
        cold.reserve_synthetic(
            registry, call,
            OneShotAuthorization(token_id, call.request_id, 200),
            occurrence_id=occurrence, now_ms=100,
        )
    assert SyntheticOccurrenceStore(path).count_synthetic() == 1
    assert b"private-token-must-not-persist" not in path.read_bytes()
