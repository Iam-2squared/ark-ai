"""Cold-process synthetic trigger clock/interval/replay review.

An existing durable preparation prevents rollback-clock and too-early
preparations on a separate interpreter. It does not issue notifications,
authenticate time, grant consent, or execute a ToolBackend.
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


def _policy() -> SyntheticTriggerPolicy:
    return SyntheticTriggerPolicy(
        "synthetic-owner", "private", "synthetic-definition",
        1, "pinned-policy", 5, 1000, 8,
    )


def _cold_prepare(path: str, candidate_ms: int, messages) -> None:
    try:
        ledger = SyntheticProactiveLedger(Path(path))
        try:
            result = ledger.prepare(
                _policy(), source_digest="a" * 64,
                observation_digest="c" * 64,
                observed_at_ms=90, now_ms=candidate_ms,
            )
        except SyntheticTriggerRejected as exc:
            messages.put(("rejected", str(exc)))
        else:
            assert result.notification_authorized is False
            assert result.dispatch_authorized is False
            assert result.automatic_replay_authorized is False
            messages.put(("prepared", result.trigger_id))
    except Exception as exc:
        messages.put(("error", repr(exc)))


@pytest.mark.parametrize(
    ("candidate_ms", "expected", "reason", "expected_count"),
    (
        (99, "rejected", "clock regressed", 1),
        (104, "rejected", "minimum preparation interval", 1),
        (105, "prepared", None, 2),
    ),
)
def test_cold_process_enforces_retained_trigger_clock_and_interval(
    tmp_path, candidate_ms, expected, reason, expected_count,
):
    path = tmp_path / "proactive-cold-clock.sqlite3"
    original = SyntheticProactiveLedger(path)
    first = original.prepare(
        _policy(), source_digest="a" * 64,
        observation_digest="b" * 64,
        observed_at_ms=90, now_ms=100,
    )
    assert first.notification_authorized is False
    assert original.count() == 1

    context = get_context("spawn")
    messages = context.Queue()
    child = context.Process(
        target=_cold_prepare, args=(str(path), candidate_ms, messages),
    )
    try:
        child.start()
        outcome = messages.get(timeout=35)
    except Empty as exc:
        pytest.fail(f"cold synthetic scheduler worker did not respond: {exc}")
    finally:
        child.join(timeout=20)
        if child.is_alive():
            child.terminate()
            child.join(timeout=5)
        messages.close()
        messages.join_thread()

    assert child.exitcode == 0
    assert outcome[0] == expected, outcome
    if reason is not None:
        assert reason in outcome[1]
    else:
        assert outcome[1] != first.trigger_id
    assert SyntheticProactiveLedger(path).count() == expected_count
