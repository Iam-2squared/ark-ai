"""Two independent fixture writers cannot cross a persisted trigger interval.

Synthetic trigger preparation is a local, content-minimized SQLite marker, not
notification delivery, tool execution, a trusted clock, or user consent.
"""

from __future__ import annotations

import subprocess
import sys
import time

import pytest

from ark.proactive_synthetic_review import SyntheticProactiveLedger

_CHILD = r"""
import pathlib
import sys
import time

from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerPolicy,
    SyntheticTriggerRejected,
)

path = pathlib.Path(sys.argv[1])
ready = pathlib.Path(sys.argv[2])
release = pathlib.Path(sys.argv[3])
source = sys.argv[4]
policy = SyntheticTriggerPolicy(
    "synthetic-trigger-owner", "private", "fixture-definition", 1,
    "policy-v1", 100, 1000, 5,
)
ready.touch()
deadline = time.monotonic() + 30
while not release.exists():
    if time.monotonic() >= deadline:
        sys.exit("trigger contender barrier timed out")
    time.sleep(0.02)
try:
    receipt = SyntheticProactiveLedger(path).prepare(
        policy, source_digest=source, observation_digest="f" * 64,
        observed_at_ms=900, now_ms=1000,
    )
except SyntheticTriggerRejected:
    print("DENIED", flush=True)
else:
    assert not receipt.notification_authorized
    assert not receipt.dispatch_authorized
    assert not receipt.automatic_replay_authorized
    print("PREPARED", flush=True)
"""


@pytest.mark.parametrize("same_source", (True, False))
def test_cross_process_trigger_interval_survives_cold_reopen(
    tmp_path, same_source: bool,
) -> None:
    path = tmp_path / "synthetic-trigger-concurrent.sqlite3"
    assert SyntheticProactiveLedger(path).count() == 0
    ready = (tmp_path / "writer-a.ready", tmp_path / "writer-b.ready")
    release = tmp_path / "release"
    sources = ("a" * 64, "a" * 64 if same_source else "b" * 64)
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", _CHILD, str(path), str(ready[i]),
             str(release), sources[i]],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        for i in range(2)
    ]
    results = []
    try:
        deadline = time.monotonic() + 30
        while not all(marker.exists() for marker in ready):
            if any(process.poll() is not None for process in processes):
                raise AssertionError("proactive contender ended before barrier")
            if time.monotonic() >= deadline:
                raise AssertionError("proactive barrier timed out")
            time.sleep(0.02)
        release.touch()
        for process in processes:
            stdout, stderr = process.communicate(timeout=40)
            results.append((process.returncode, stdout.strip(), stderr))
    finally:
        release.touch()
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate()

    assert all(code == 0 and not err for code, _, err in results), results
    assert sorted(msg for _, msg, _ in results) == ["DENIED", "PREPARED"]
    assert SyntheticProactiveLedger(path).count() == 1

    # This is an offline interval fence, not authorization or scheduling.
    # Once the synthetic interval has elapsed, a distinct occurrence can be
    # persisted without replaying the first one.
    from ark.proactive_synthetic_review import SyntheticTriggerPolicy

    policy = SyntheticTriggerPolicy(
        "synthetic-trigger-owner", "private", "fixture-definition", 1,
        "policy-v1", 100, 1000, 5,
    )
    receipt = SyntheticProactiveLedger(path).prepare(
        policy, source_digest="c" * 64, observation_digest="f" * 64,
        observed_at_ms=1000, now_ms=1100,
    )
    assert receipt.notification_authorized is False
    assert receipt.dispatch_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert SyntheticProactiveLedger(path).count() == 2
