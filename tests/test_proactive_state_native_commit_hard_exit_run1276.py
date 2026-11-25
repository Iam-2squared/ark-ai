"""Run1276: proactive state survives process exit after native SQLite COMMIT.

Synthetic local SQLite only. This does not prove fsync/power-loss durability,
trusted time, notification consent, dispatch authority, or external effects.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

from ark.proactive_state_ledger import (
    SyntheticProactivePolicy,
    SyntheticProactiveStateConflict,
    SyntheticProactiveStateLedger,
)

_PRIVATE = "run1276-private-observation-must-not-be-persisted"

_CHILD = r"""
import os
import sqlite3
import sys
from pathlib import Path

import ark.proactive_state_ledger as module
from ark.proactive_state_ledger import (
    SyntheticProactivePolicy,
    SyntheticProactiveStateLedger,
)

path = Path(sys.argv[1])
policy = SyntheticProactivePolicy(
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
ledger = SyntheticProactiveStateLedger(path)
native_connect = sqlite3.connect
target_uri = path.resolve().as_uri() + "?mode=rw"


class ExitAfterCommit:
    def __init__(self, connection):
        self.connection = connection

    def commit(self):
        self.connection.commit()
        # Native SQLite COMMIT returned; the public evaluate() call has not.
        os._exit(76)

    def __getattr__(self, name):
        return getattr(self.connection, name)


def controlled_connect(database, *args, **kwargs):
    connection = native_connect(database, *args, **kwargs)
    if database == target_uri:
        return ExitAfterCommit(connection)
    return connection


# The production protocol requires sqlite3.connect and its retained factory
# to be the same object. Replace both only in this disposable child so the
# test can observe the native COMMIT boundary without changing production.
sqlite3.connect = controlled_connect
module._ORIGINAL_CONNECT = controlled_connect

ledger.evaluate(
    policy,
    observation_digest="a" * 64,
    observed_at_ms=10,
    now_ms=10,
    expected_revision=0,
)
os._exit(77)
"""


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


def _assert_private_absent(path: Path) -> None:
    for artifact in (
        path,
        path.with_name(path.name + "-wal"),
        path.with_name(path.name + "-shm"),
    ):
        if artifact.exists():
            assert _PRIVATE.encode("utf-8") not in artifact.read_bytes()


def test_native_commit_hard_exit_recovers_one_preview_without_replay_run1276(
    tmp_path: Path,
) -> None:
    path = tmp_path / "proactive-native-commit-hard-exit.sqlite3"
    policy = _policy()
    initial = SyntheticProactiveStateLedger(path)
    assert initial.read_state(policy) is None

    child = subprocess.run(
        [sys.executable, "-c", _CHILD, str(path)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert child.returncode == 76, child.stdout + child.stderr

    cold = SyntheticProactiveStateLedger(path)
    recovered = cold.read_state(policy)
    assert recovered is not None
    assert recovered.revision == 1
    assert recovered.last_decision == "ELIGIBLE_PREVIEW"
    assert recovered.last_observation_digest == hashlib.sha256(b"").hexdigest()[:0] + "a" * 64
    assert recovered.last_observed_at_ms == 10
    assert recovered.last_evaluated_at_ms == 10
    assert recovered.last_proposal_at_ms == 10
    assert recovered.updated_at_ms == 10
    assert recovered.window_proposal_times == (10,)
    assert recovered.notification_authorized is False
    assert recovered.dispatch_authorized is False
    assert recovered.trusted_clock_verified is False
    assert recovered.automatic_replay_authorized is False
    assert recovered.consent_verified is False
    assert cold.count() == 1
    _assert_private_absent(path)

    with pytest.raises(SyntheticProactiveStateConflict):
        cold.evaluate(
            policy,
            observation_digest="b" * 64,
            observed_at_ms=20,
            now_ms=20,
            expected_revision=0,
        )
    assert cold.read_state(policy) == recovered
    assert cold.count() == 1

    unchanged = cold.evaluate(
        policy,
        observation_digest="a" * 64,
        observed_at_ms=20,
        now_ms=20,
        expected_revision=recovered.revision,
    )
    assert unchanged.revision == 2
    assert unchanged.last_decision == "UNCHANGED"
    assert unchanged.last_evaluated_at_ms == 20
    assert unchanged.last_proposal_at_ms == 10
    assert unchanged.window_proposal_times == (10,)
    assert cold.count() == 1
    _assert_private_absent(path)
