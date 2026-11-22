"""Run1091: restart-safe synthetic proactive proposal state and CAS tests."""

from __future__ import annotations

import hashlib
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Barrier

import pytest

from ark.proactive_state_ledger import (
    SyntheticProactivePolicy,
    SyntheticProactiveStateConflict,
    SyntheticProactiveStateLedger,
    SyntheticProactiveStateRejected,
)


def _digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _policy(**overrides) -> SyntheticProactivePolicy:
    values = {
        "owner": "owner-a",
        "namespace": "personal",
        "definition_id": "daily-summary",
        "revision": 1,
        "policy_revision": "policy-v1",
        "minimum_interval_ms": 100,
        "cooldown_ms": 200,
        "rolling_window_ms": 1000,
        "max_previews_per_window": 2,
    }
    values.update(overrides)
    return SyntheticProactivePolicy(**values)


def _evaluate(
    ledger: SyntheticProactiveStateLedger,
    policy: SyntheticProactivePolicy,
    observation: str,
    now: int,
    expected_revision: int,
):
    return ledger.evaluate(
        policy,
        observation_digest=_digest(observation),
        observed_at_ms=now,
        now_ms=now,
        expected_revision=expected_revision,
    )


def test_first_preview_is_durable_content_minimized_and_denial_only(tmp_path: Path):
    path = tmp_path / "proactive.sqlite"
    ledger = SyntheticProactiveStateLedger(path)
    policy = _policy()
    state = _evaluate(ledger, policy, "private observation alpha", 0, 0)

    assert state.revision == 1
    assert state.last_decision == "ELIGIBLE_PREVIEW"
    assert state.last_proposal_at_ms == 0
    assert state.window_proposal_times == (0,)
    assert state.notification_authorized is False
    assert state.dispatch_authorized is False
    assert state.trusted_clock_verified is False
    assert state.automatic_replay_authorized is False
    assert state.consent_verified is False
    assert ledger.read_state(policy) == state
    assert ledger.count() == 1
    assert b"private observation alpha" not in path.read_bytes()


def test_cooldown_persists_observation_digest_and_exact_window_boundary(tmp_path: Path):
    ledger = SyntheticProactiveStateLedger(tmp_path / "proactive.sqlite")
    policy = _policy()

    first = _evaluate(ledger, policy, "A", 0, 0)
    too_soon = _evaluate(ledger, policy, "B", 50, first.revision)
    assert too_soon.last_decision == "TOO_SOON"
    assert too_soon.last_observation_digest == first.last_observation_digest
    assert too_soon.last_evaluated_at_ms == 0

    cooldown = _evaluate(ledger, policy, "B", 100, too_soon.revision)
    assert cooldown.last_decision == "COOLDOWN"
    assert cooldown.last_observation_digest == _digest("B")
    assert cooldown.last_evaluated_at_ms == 100
    assert cooldown.last_proposal_at_ms == 0

    second = _evaluate(ledger, policy, "C", 200, cooldown.revision)
    assert second.last_decision == "ELIGIBLE_PREVIEW"
    assert second.window_proposal_times == (0, 200)

    budgeted = _evaluate(ledger, policy, "D", 400, second.revision)
    assert budgeted.last_decision == "WINDOW_BUDGET"
    assert budgeted.last_observation_digest == _digest("D")

    boundary = _evaluate(ledger, policy, "E", 1000, budgeted.revision)
    assert boundary.last_decision == "ELIGIBLE_PREVIEW"
    assert boundary.window_proposal_times == (200, 1000)


def test_unchanged_observation_stays_suppressed_after_cooldown(tmp_path: Path):
    ledger = SyntheticProactiveStateLedger(tmp_path / "proactive.sqlite")
    policy = _policy()
    first = _evaluate(ledger, policy, "A", 0, 0)
    cooled = _evaluate(ledger, policy, "B", 100, first.revision)

    unchanged = _evaluate(ledger, policy, "B", 300, cooled.revision)
    assert unchanged.last_decision == "UNCHANGED"
    assert unchanged.last_observation_digest == _digest("B")
    assert unchanged.last_proposal_at_ms == 0
    assert unchanged.window_proposal_times == (0,)


def test_restart_recovers_state_and_stale_revision_cannot_overwrite(tmp_path: Path):
    path = tmp_path / "proactive.sqlite"
    policy = _policy()
    first = _evaluate(
        SyntheticProactiveStateLedger(path), policy, "A", 0, 0,
    )
    reopened = SyntheticProactiveStateLedger(path)

    assert reopened.read_state(policy) == first
    with pytest.raises(SyntheticProactiveStateConflict):
        _evaluate(reopened, policy, "B", 100, 0)

    second = _evaluate(reopened, policy, "B", 100, first.revision)
    assert second.revision == 2
    assert second.last_decision == "COOLDOWN"


def test_two_store_instances_have_one_cas_winner(tmp_path: Path):
    path = tmp_path / "proactive.sqlite"
    policy = _policy()
    first = _evaluate(SyntheticProactiveStateLedger(path), policy, "A", 0, 0)
    stores = (SyntheticProactiveStateLedger(path), SyntheticProactiveStateLedger(path))
    barrier = Barrier(2)

    def attempt(store: SyntheticProactiveStateLedger, observation: str):
        barrier.wait(timeout=5)
        try:
            return _evaluate(store, policy, observation, 100, first.revision)
        except SyntheticProactiveStateConflict:
            return "conflict"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(
            lambda pair: attempt(*pair),
            ((stores[0], "B"), (stores[1], "C")),
        ))

    assert sum(result != "conflict" for result in results) == 1
    assert sum(result == "conflict" for result in results) == 1
    assert SyntheticProactiveStateLedger(path).read_state(policy).revision == 2


def test_clock_and_observation_regression_fail_closed(tmp_path: Path):
    ledger = SyntheticProactiveStateLedger(tmp_path / "proactive.sqlite")
    policy = _policy()
    first = _evaluate(ledger, policy, "A", 100, 0)

    with pytest.raises(SyntheticProactiveStateRejected, match="clock regressed"):
        _evaluate(ledger, policy, "B", 99, first.revision)
    with pytest.raises(SyntheticProactiveStateRejected, match="observation clock regressed"):
        ledger.evaluate(
            policy,
            observation_digest=_digest("B"),
            observed_at_ms=99,
            now_ms=101,
            expected_revision=first.revision,
        )
    assert ledger.read_state(policy) == first


def test_policy_revision_isolated_and_exact_integer_inputs_required(tmp_path: Path):
    ledger = SyntheticProactiveStateLedger(tmp_path / "proactive.sqlite")
    policy = _policy()
    first = _evaluate(ledger, policy, "A", 0, 0)
    changed_policy = _policy(policy_revision="policy-v2")

    second = _evaluate(ledger, changed_policy, "A", 0, 0)
    assert second.revision == 1
    assert second.policy_digest != first.policy_digest
    assert ledger.count() == 2

    with pytest.raises(SyntheticProactiveStateRejected, match="exact bounded integer"):
        ledger.evaluate(
            policy,
            observation_digest=_digest("B"),
            observed_at_ms=True,
            now_ms=100,
            expected_revision=first.revision,
        )
    with pytest.raises(SyntheticProactiveStateRejected, match="exact bounded integer"):
        ledger.evaluate(
            policy,
            observation_digest=_digest("B"),
            observed_at_ms=100,
            now_ms=100,
            expected_revision=True,
        )
    with pytest.raises(SyntheticProactiveStateRejected, match="canonical observation digest"):
        ledger.evaluate(
            policy,
            observation_digest="A" * 64,
            observed_at_ms=100,
            now_ms=100,
            expected_revision=first.revision,
        )


def test_same_millisecond_previews_remain_counted_with_zero_intervals(tmp_path: Path):
    ledger = SyntheticProactiveStateLedger(tmp_path / "proactive.sqlite")
    policy = _policy(
        minimum_interval_ms=0,
        cooldown_ms=0,
        max_previews_per_window=3,
    )
    first = _evaluate(ledger, policy, "A", 0, 0)
    second = _evaluate(ledger, policy, "B", 0, first.revision)

    assert second.last_decision == "ELIGIBLE_PREVIEW"
    assert second.window_proposal_times == (0, 0)
    assert ledger.read_state(policy) == second


def test_schema_drift_and_row_digest_corruption_are_refused(tmp_path: Path):
    path = tmp_path / "proactive.sqlite"
    ledger = SyntheticProactiveStateLedger(path)
    policy = _policy()
    _evaluate(ledger, policy, "A", 0, 0)

    with sqlite3.connect(path) as conn:
        conn.execute(
            "UPDATE synthetic_proactive_states "
            "SET last_observation_digest=?",
            (_digest("tampered"),),
        )
    with pytest.raises(SyntheticProactiveStateRejected, match="digest mismatch"):
        ledger.read_state(policy)

    clean_path = tmp_path / "schema-drift.sqlite"
    clean = SyntheticProactiveStateLedger(clean_path)
    with sqlite3.connect(clean_path) as conn:
        conn.execute("ALTER TABLE synthetic_proactive_states ADD COLUMN injected TEXT")
    with pytest.raises(SyntheticProactiveStateRejected, match="schema changed"):
        clean.read_state(policy)


def test_read_only_reopen_does_not_recreate_a_missing_database(tmp_path: Path):
    path = tmp_path / "missing-after-init.sqlite"
    ledger = SyntheticProactiveStateLedger(path)
    path.unlink()

    with pytest.raises(sqlite3.OperationalError):
        ledger.read_state(_policy())
    assert not path.exists()


def test_future_observation_and_policy_control_characters_are_denied(tmp_path: Path):
    ledger = SyntheticProactiveStateLedger(tmp_path / "proactive.sqlite")
    with pytest.raises(SyntheticProactiveStateRejected, match="control delimiter"):
        _policy(owner="owner\\x00spoof")

    with pytest.raises(SyntheticProactiveStateRejected, match="future observation"):
        ledger.evaluate(
            _policy(),
            observation_digest=_digest("A"),
            observed_at_ms=101,
            now_ms=100,
            expected_revision=0,
        )
