"""Run1441: proactive state first-open and revision CAS across processes.

Synthetic local SQLite only. No notification, consent, trusted-time, timer,
dispatch, replay, or external-effect authority is established by these tests.
"""

from __future__ import annotations

import hashlib
from multiprocessing import get_context
from pathlib import Path

from ark.proactive_state_ledger import (
    SyntheticProactivePolicy,
    SyntheticProactiveStateConflict,
    SyntheticProactiveStateLedger,
)


def _policy() -> SyntheticProactivePolicy:
    return SyntheticProactivePolicy(
        owner="synthetic-owner",
        namespace="private",
        definition_id="daily-summary",
        revision=1,
        policy_revision="fixture-v1",
        minimum_interval_ms=0,
        cooldown_ms=0,
        rolling_window_ms=1000,
        max_previews_per_window=4,
    )


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _initialize_worker(path: str, ready, release, results) -> None:
    ready.put("ready")
    if not release.wait(timeout=45):
        raise RuntimeError("first-open release timed out")
    ledger = SyntheticProactiveStateLedger(Path(path))
    results.put(("ok", ledger.count()))


def _evaluate_worker(
    path: str,
    observation_digest: str,
    observed_at_ms: int,
    now_ms: int,
    expected_revision: int,
    ready,
    release,
    results,
) -> None:
    ledger = SyntheticProactiveStateLedger(Path(path))
    ready.put("ready")
    if not release.wait(timeout=45):
        raise RuntimeError("CAS release timed out")
    try:
        state = ledger.evaluate(
            _policy(),
            observation_digest=observation_digest,
            observed_at_ms=observed_at_ms,
            now_ms=now_ms,
            expected_revision=expected_revision,
        )
    except SyntheticProactiveStateConflict:
        results.put(("conflict",))
    else:
        results.put((
            "success",
            state.revision,
            state.last_observation_digest,
            state.last_decision,
            state.window_proposal_times,
        ))


def _run_two_processes(
    target,
    per_process_args: tuple[tuple[object, ...], tuple[object, ...]],
) -> list[tuple[object, ...]]:
    context = get_context("spawn")
    ready = context.Queue()
    results = context.Queue()
    release = context.Event()
    processes = [
        context.Process(target=target, args=(*args, ready, release, results))
        for args in per_process_args
    ]
    try:
        for process in processes:
            process.start()
        assert [ready.get(timeout=60) for _ in processes] == ["ready", "ready"]
        release.set()
        outcomes = [results.get(timeout=60) for _ in processes]
        for process in processes:
            process.join(timeout=60)
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
        assert [process.exitcode for process in processes] == [0, 0]
        return outcomes
    finally:
        release.set()
        for process in processes:
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
        ready.close()
        results.close()


def _assert_one_winner(outcomes: list[tuple[object, ...]]) -> tuple[object, ...]:
    assert sorted(outcome[0] for outcome in outcomes) == ["conflict", "success"]
    winner = next(outcome for outcome in outcomes if outcome[0] == "success")
    assert len(winner) == 5
    return winner


def test_two_process_first_open_converges_on_one_valid_schema_run1441(tmp_path: Path):
    path = tmp_path / "proactive-first-open-race.sqlite3"
    outcomes = _run_two_processes(
        _initialize_worker,
        ((str(path),), (str(path),)),
    )
    assert sorted(outcomes) == [("ok", 0), ("ok", 0)]
    cold = SyntheticProactiveStateLedger(path)
    assert cold.count() == 0
    assert cold.read_state(_policy()) is None


def test_two_process_genesis_cas_has_exactly_one_winner_run1441(tmp_path: Path):
    path = tmp_path / "proactive-genesis-cas-race.sqlite3"
    ledger = SyntheticProactiveStateLedger(path)
    policy = _policy()
    assert ledger.read_state(policy) is None

    digests = (_digest("private-observation-a"), _digest("private-observation-b"))
    outcomes = _run_two_processes(
        _evaluate_worker,
        (
            (str(path), digests[0], 100, 100, 0),
            (str(path), digests[1], 100, 100, 0),
        ),
    )
    winner = _assert_one_winner(outcomes)

    recovered = SyntheticProactiveStateLedger(path)
    state = recovered.read_state(policy)
    assert state is not None
    assert state.revision == 1
    assert state.last_decision == "ELIGIBLE_PREVIEW"
    assert state.last_observation_digest == winner[2]
    assert state.last_observation_digest in digests
    assert state.window_proposal_times == (100,)
    assert recovered.count() == 1
    assert b"private-observation-" not in path.read_bytes()


def test_two_process_same_revision_update_has_exactly_one_winner_run1441(tmp_path: Path):
    path = tmp_path / "proactive-update-cas-race.sqlite3"
    ledger = SyntheticProactiveStateLedger(path)
    policy = _policy()
    initial = ledger.evaluate(
        policy,
        observation_digest=_digest("private-genesis-observation"),
        observed_at_ms=100,
        now_ms=100,
        expected_revision=0,
    )
    assert initial.revision == 1

    candidates = (
        _digest("private-update-observation-a"),
        _digest("private-update-observation-b"),
    )
    outcomes = _run_two_processes(
        _evaluate_worker,
        (
            (str(path), candidates[0], 200, 200, 1),
            (str(path), candidates[1], 200, 200, 1),
        ),
    )
    winner = _assert_one_winner(outcomes)

    cold = SyntheticProactiveStateLedger(path)
    recovered = cold.read_state(policy)
    assert recovered is not None
    assert recovered.revision == 2
    assert recovered.last_decision == "ELIGIBLE_PREVIEW"
    assert recovered.last_observation_digest == winner[2]
    assert recovered.last_observation_digest in candidates
    assert recovered.window_proposal_times == (100, 200)
    assert cold.count() == 1
    assert b"private-update-observation-" not in path.read_bytes()
