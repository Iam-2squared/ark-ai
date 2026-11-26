"""Run1458: proactive-state COMMIT survives exit with a pinned WAL reader."""

from __future__ import annotations

import hashlib
import os
import sqlite3
import sys
from contextlib import closing
from multiprocessing import get_context
from pathlib import Path

import pytest

from ark.proactive_state_ledger import (
    SyntheticProactivePolicy,
    SyntheticProactiveStateConflict,
    SyntheticProactiveStateLedger,
)

_PRIVATE = "private-observation-after-commit-run1458"


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


def _snapshot(connection: sqlite3.Connection) -> tuple[int]:
    return connection.execute(
        "SELECT COUNT(*) FROM synthetic_proactive_states"
    ).fetchone()


def _exit_after_native_commit(database: str) -> None:
    ledger = SyntheticProactiveStateLedger(Path(database))
    policy = _policy()
    evaluate_code = SyntheticProactiveStateLedger.evaluate.__code__

    def exit_after_commit(frame, event, argument) -> None:
        if (
            event == "c_return"
            and frame.f_code is evaluate_code
            and getattr(argument, "__name__", None) == "commit"
        ):
            # Native SQLite COMMIT returned. Exit before receipt construction,
            # post-COMMIT checks or Python connection cleanup can run.
            os._exit(74)

    sys.setprofile(exit_after_commit)
    ledger.evaluate(
        policy,
        observation_digest=_digest(_PRIVATE),
        observed_at_ms=100,
        now_ms=100,
        expected_revision=0,
    )
    os._exit(75)


def test_proactive_state_commit_survives_hard_exit_with_pinned_wal_reader(
    tmp_path: Path,
) -> None:
    path = tmp_path / "proactive-state-pinned-wal-reader-run1458.sqlite3"
    policy = _policy()
    ledger = SyntheticProactiveStateLedger(path)
    assert ledger.read_state(policy) is None

    # This ledger deliberately leaves SQLite journal-mode selection to its
    # environment. Set WAL explicitly so a pinned reader tests WAL retention,
    # rather than making a DELETE-journal writer wait on a reader lock.
    with closing(
        sqlite3.connect(path, timeout=10, isolation_level=None)
    ) as setup:
        journal_mode = setup.execute("PRAGMA journal_mode=WAL").fetchone()
    assert journal_mode == ("wal",)

    keeper = sqlite3.connect(path, timeout=10, isolation_level=None)
    keeper_open = True
    try:
        keeper.execute("PRAGMA query_only=ON")
        keeper.execute("BEGIN")
        before = (0,)
        assert _snapshot(keeper) == before

        process = get_context("spawn").Process(
            target=_exit_after_native_commit,
            args=(str(path),),
        )
        process.start()
        process.join(timeout=60)
        if process.is_alive():
            process.terminate()
            process.join(timeout=5)
            pytest.fail("proactive state pinned-reader worker did not terminate")
        assert process.exitcode == 74

        # The pinned snapshot must retain the empty prefix even though the
        # writer's committed revision is now present in the WAL.
        assert _snapshot(keeper) == before
        with closing(
            sqlite3.connect(path, timeout=0.2, isolation_level=None)
        ) as checkpoint_connection:
            blocked = checkpoint_connection.execute(
                "PRAGMA wal_checkpoint(TRUNCATE)"
            ).fetchone()
        assert blocked is not None
        assert blocked[0] == 1 or blocked[1] != blocked[2]

        keeper.rollback()
        keeper.close()
        keeper_open = False

        cold = SyntheticProactiveStateLedger(path)
        recovered = cold.read_state(policy)
        assert recovered is not None
        assert recovered.revision == 1
        assert recovered.last_observation_digest == _digest(_PRIVATE)
        assert recovered.last_observed_at_ms == 100
        assert recovered.last_evaluated_at_ms == 100
        assert recovered.last_decision == "ELIGIBLE_PREVIEW"
        assert recovered.window_proposal_times == (100,)
        assert recovered.notification_authorized is False
        assert recovered.dispatch_authorized is False
        assert recovered.trusted_clock_verified is False
        assert recovered.automatic_replay_authorized is False
        assert recovered.consent_verified is False
        assert cold.count() == 1

        # A lost receipt must be reconciled by reading revision 1. Replaying
        # the genesis CAS cannot create a second proposal.
        with pytest.raises(SyntheticProactiveStateConflict):
            cold.evaluate(
                policy,
                observation_digest=_digest("different-private-observation"),
                observed_at_ms=101,
                now_ms=101,
                expected_revision=0,
            )
        after_retry = cold.read_state(policy)
        assert after_retry is not None
        assert after_retry.revision == 1
        assert after_retry.last_observation_digest == _digest(_PRIVATE)
        assert cold.count() == 1

        with closing(sqlite3.connect(path, timeout=10)) as connection:
            assert connection.execute("PRAGMA quick_check").fetchone() == ("ok",)
            assert connection.execute("PRAGMA user_version").fetchone() == (1,)
            assert connection.execute(
                "SELECT COUNT(*) FROM synthetic_proactive_states"
            ).fetchone() == (1,)
            checkpoint = connection.execute(
                "PRAGMA wal_checkpoint(TRUNCATE)"
            ).fetchone()
            assert checkpoint is not None
            assert checkpoint[0] == 0
            assert checkpoint[1] == checkpoint[2]

        persisted = b"".join(
            item.read_bytes() for item in tmp_path.iterdir() if item.is_file()
        )
        assert _PRIVATE.encode("utf-8") not in persisted
    finally:
        if keeper_open:
            if keeper.in_transaction:
                keeper.rollback()
            keeper.close()
