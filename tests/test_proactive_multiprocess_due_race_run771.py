"""Competing disconnected proactive preparations share a durable time fence.

Only disposable hash-only local markers; no notifications, tool execution,
trusted time or consent are created by these synthetic worker processes.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)


def _policy(owner: str = "owner-a") -> SyntheticTriggerPolicy:
    return SyntheticTriggerPolicy(
        owner, "private", "definition", 1, "reviewed-local", 5, 1000, 8,
    )


_CHILD = """
import sys
from pathlib import Path
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger, SyntheticTriggerPolicy, SyntheticTriggerRejected,
)
policy = SyntheticTriggerPolicy(
    sys.argv[2], "private", "definition", 1, "reviewed-local", 5, 1000, 8,
)
try:
    receipt = SyntheticProactiveLedger(Path(sys.argv[1])).prepare(
        policy, source_digest="a" * 64,
        observation_digest=sys.argv[3] * 64,
        observed_at_ms=90, now_ms=100,
    )
except SyntheticTriggerRejected:
    sys.exit(4)
assert receipt.notification_authorized is False
assert receipt.dispatch_authorized is False
assert receipt.automatic_replay_authorized is False
"""


@pytest.mark.parametrize("same_observation", (True, False))
def test_two_processes_one_owner_only_one_preparation(
    tmp_path: Path, same_observation: bool,
) -> None:
    path = tmp_path / "due-race.sqlite"
    SyntheticProactiveLedger(path)
    values = ("b", "b" if same_observation else "c")
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", _CHILD, str(path), "owner-a", value],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        for value in values
    ]
    outputs = [process.communicate(timeout=25) for process in processes]
    assert sorted(p.returncode for p in processes) == [0, 4], outputs
    assert SyntheticProactiveLedger(path).count() == 1

    cold = SyntheticProactiveLedger(path)
    with pytest.raises(SyntheticTriggerRejected, match="minimum preparation interval"):
        cold.prepare(
            _policy(), source_digest="a" * 64,
            observation_digest="d" * 64, observed_at_ms=90, now_ms=104,
        )
    assert SyntheticProactiveLedger(path).count() == 1
    assert b"owner-a" not in path.read_bytes()


def test_two_owners_are_not_collapsed_into_one_due_fence(tmp_path: Path) -> None:
    path = tmp_path / "owner-due-race.sqlite"
    SyntheticProactiveLedger(path)
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", _CHILD, str(path), owner, "b"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        for owner in ("owner-a", "owner-b")
    ]
    outputs = [process.communicate(timeout=25) for process in processes]
    assert [p.returncode for p in processes] == [0, 0], outputs
    assert SyntheticProactiveLedger(path).count() == 2
    data = path.read_bytes()
    assert b"owner-a" not in data
    assert b"owner-b" not in data
