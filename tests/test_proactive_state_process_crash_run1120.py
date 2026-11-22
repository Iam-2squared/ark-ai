"""Run1120: proactive eligibility state survives a real process exit."""

from __future__ import annotations

import hashlib
import os
from multiprocessing import get_context
from pathlib import Path

import pytest

from ark.proactive_state_ledger import (
    SyntheticProactivePolicy,
    SyntheticProactiveStateConflict,
    SyntheticProactiveStateLedger,
)


def _policy() -> SyntheticProactivePolicy:
    return SyntheticProactivePolicy(
        owner="owner-a",
        namespace="personal",
        definition_id="daily-summary",
        revision=1,
        policy_revision="policy-v1",
        minimum_interval_ms=100,
        cooldown_ms=200,
        rolling_window_ms=1000,
        max_previews_per_window=2,
    )


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _evaluate_then_exit(path: str) -> None:
    ledger = SyntheticProactiveStateLedger(Path(path))
    ledger.evaluate(
        _policy(),
        observation_digest=_digest("private-observation"),
        observed_at_ms=10,
        now_ms=10,
        expected_revision=0,
    )
    # Simulate abrupt process death after the durable state transition returns.
    os._exit(47)


def test_process_exit_preserves_one_preview_and_requires_cas_readback(
    tmp_path: Path,
) -> None:
    path = tmp_path / "proactive-process-crash.sqlite3"
    policy = _policy()
    initial = SyntheticProactiveStateLedger(path)
    assert initial.read_state(policy) is None

    child = get_context("spawn").Process(
        target=_evaluate_then_exit,
        args=(str(path),),
    )
    child.start()
    child.join(timeout=40)
    if child.is_alive():
        child.terminate()
        child.join(timeout=5)
    assert child.exitcode == 47, "child did not exit after the durable preview transition"

    cold = SyntheticProactiveStateLedger(path)
    recovered = cold.read_state(policy)
    assert recovered is not None
    assert recovered.revision == 1
    assert recovered.last_decision == "ELIGIBLE_PREVIEW"
    assert recovered.last_observation_digest == _digest("private-observation")
    assert recovered.window_proposal_times == (10,)
    assert recovered.notification_authorized is False
    assert recovered.dispatch_authorized is False
    assert recovered.automatic_replay_authorized is False
    assert recovered.consent_verified is False
    assert b"private-observation" not in path.read_bytes()

    with pytest.raises(SyntheticProactiveStateConflict):
        cold.evaluate(
            policy,
            observation_digest=_digest("different-observation"),
            observed_at_ms=20,
            now_ms=20,
            expected_revision=0,
        )
    assert cold.read_state(policy) == recovered

    unchanged = cold.evaluate(
        policy,
        observation_digest=_digest("private-observation"),
        observed_at_ms=20,
        now_ms=20,
        expected_revision=recovered.revision,
    )
    assert unchanged.revision == 2
    assert unchanged.last_decision == "UNCHANGED"
    assert unchanged.window_proposal_times == (10,)
    assert cold.count() == 1
