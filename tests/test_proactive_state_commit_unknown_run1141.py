"""Run1141: proactive state quarantines ambiguous SQLite COMMIT outcomes."""

from __future__ import annotations

import subprocess
import sys

import pytest


@pytest.mark.parametrize("durable", (False, True))
def test_evaluate_commit_ack_loss_requires_readback_and_never_retries(
    tmp_path,
    durable: bool,
) -> None:
    database = tmp_path / "proactive-commit-unknown.sqlite3"
    script = r"""
import hashlib
import sqlite3
from pathlib import Path

DATABASE = Path(__DATABASE__)
DURABLE = __DURABLE__
TARGET_URI = DATABASE.resolve().as_uri() + "?mode=rw"
armed = False
commit_attempts = 0
native_connect = sqlite3.connect


class CommitBoundary:
    def __init__(self, connection):
        self.connection = connection

    def commit(self):
        global commit_attempts
        commit_attempts += 1
        if DURABLE:
            self.connection.commit()
        else:
            self.connection.rollback()
        raise sqlite3.OperationalError(
            "synthetic proactive COMMIT acknowledgement lost"
        )

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()

    def __getattr__(self, name):
        return getattr(self.connection, name)


def controlled_connect(database, *args, **kwargs):
    connection = native_connect(database, *args, **kwargs)
    if armed and database == TARGET_URI:
        return CommitBoundary(connection)
    return connection


# Install the stable fixture factory before ARK imports and captures SQLite.
sqlite3.connect = controlled_connect

from ark.proactive_state_ledger import (
    SyntheticProactivePolicy,
    SyntheticProactiveStateConflict,
    SyntheticProactiveStateLedger,
)

policy = SyntheticProactivePolicy(
    owner="fixture-owner",
    namespace="fixture-local",
    definition_id="daily-summary",
    revision=1,
    policy_revision="fixture-v1",
    minimum_interval_ms=0,
    cooldown_ms=0,
    rolling_window_ms=1000,
    max_previews_per_window=3,
)
observation_digest = hashlib.sha256(b"synthetic-observation").hexdigest()
ledger = SyntheticProactiveStateLedger(DATABASE)

armed = True
try:
    ledger.evaluate(
        policy,
        observation_digest=observation_digest,
        observed_at_ms=100,
        now_ms=100,
        expected_revision=0,
    )
except sqlite3.OperationalError as exc:
    assert "COMMIT acknowledgement lost" in str(exc)
else:
    raise AssertionError("ambiguous COMMIT unexpectedly returned a state")
finally:
    armed = False

# The failed acknowledgement must not cause an internal retry. Resolve the
# outcome only by reopening and reading the durable state in a fresh ledger.
assert commit_attempts == 1
recovered = SyntheticProactiveStateLedger(DATABASE)
state = recovered.read_state(policy)

if DURABLE:
    assert state is not None
    assert state.revision == 1
    assert state.last_decision == "ELIGIBLE_PREVIEW"
    assert state.last_observation_digest == observation_digest
    assert state.window_proposal_times == (100,)
    assert state.notification_authorized is False
    assert state.dispatch_authorized is False
    assert state.automatic_replay_authorized is False
    assert state.consent_verified is False

    # A retry with the stale genesis revision cannot create a second preview.
    try:
        recovered.evaluate(
            policy,
            observation_digest=observation_digest,
            observed_at_ms=101,
            now_ms=101,
            expected_revision=0,
        )
    except SyntheticProactiveStateConflict:
        pass
    else:
        raise AssertionError("durable ambiguous COMMIT was replayed")
    assert recovered.count() == 1
else:
    assert state is None
    assert recovered.count() == 0

assert commit_attempts == 1
"""
    script = (
        script
        .replace("__DATABASE__", repr(str(database)))
        .replace("__DURABLE__", repr(durable))
    )
    result = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=90,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
