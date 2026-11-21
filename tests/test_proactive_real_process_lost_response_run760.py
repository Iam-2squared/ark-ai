"""A lost process result cannot erase a durable proactive preparation fence.

Synthetic-only: no trusted wall clock, user notification, or tool dispatch.
"""

from __future__ import annotations

import os
from multiprocessing import get_context
from pathlib import Path

import pytest

from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _policy() -> SyntheticTriggerPolicy:
    return SyntheticTriggerPolicy(
        "fixture-owner", "private", "definition", 1,
        "pinned-policy", 5, 1000, 8,
    )


def _prepare_then_exit(path: str) -> None:
    ledger = SyntheticProactiveLedger(Path(path))
    receipt = ledger.prepare(
        _policy(), source_digest="a" * 64, observation_digest="b" * 64,
        observed_at_ms=90, now_ms=100,
    )
    assert receipt.notification_authorized is False
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    os._exit(0)  # A durable preparation exists, but caller got no receipt.


@pytest.mark.parametrize(
    ("now_ms", "message"),
    (
        (99, "clock regressed"),
        (104, "minimum preparation interval"),
    ),
)
def test_proactive_lost_response_cannot_bypass_cold_time_fence(
    tmp_path: Path, now_ms, message,
):
    path = tmp_path / "proactive-lost-response.sqlite3"
    SyntheticProactiveLedger(path)
    child = get_context("spawn").Process(
        target=_prepare_then_exit, args=(str(path),),
    )
    child.start()
    child.join(timeout=35)
    if child.is_alive():
        child.terminate()
        child.join(timeout=5)
    assert child.exitcode == 0

    cold = SyntheticProactiveLedger(path)
    assert cold.count() == 1
    with pytest.raises(SyntheticTriggerRejected, match=message):
        cold.prepare(
            _policy(), source_digest="a" * 64,
            observation_digest="c" * 64,
            observed_at_ms=90, now_ms=now_ms,
        )
    assert SyntheticProactiveLedger(path).count() == 1
    assert b"fixture-owner" not in path.read_bytes()
