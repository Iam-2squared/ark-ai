"""Independent processes test inert proactive preparation concurrency.

All data are fixed fake digests. Only disposable SQLite and local subprocesses
are used. A prepared marker never sends a notification or executes a Tool.
"""

import sqlite3
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
gate = pathlib.Path(sys.argv[2])
ready = pathlib.Path(sys.argv[3])
owner = sys.argv[4]
revision = int(sys.argv[5])
observation_digest = sys.argv[6]
ledger = SyntheticProactiveLedger(path)
policy = SyntheticTriggerPolicy(
    owner=owner,
    namespace="fixture",
    definition_id="local-check",
    revision=revision,
    policy_revision="fixture-v1",
    minimum_interval_ms=100,
    rolling_window_ms=10000,
    max_preparations_per_window=1,
)
ready.touch()
deadline = time.monotonic() + 25
while not gate.exists():
    if time.monotonic() >= deadline:
        sys.exit("proactive fixture gate timed out")
    time.sleep(0.02)
try:
    receipt = ledger.prepare(
        policy,
        source_digest="a" * 64,
        observation_digest=observation_digest,
        observed_at_ms=1000,
        now_ms=1001,
    )
except SyntheticTriggerRejected as exc:
    if not any(fragment in str(exc) for fragment in (
        "minimum preparation interval",
        "rolling preparation budget",
        "duplicate synthetic trigger occurrence",
    )):
        raise
    print("BLOCKED", flush=True)
else:
    assert not receipt.notification_authorized
    assert not receipt.dispatch_authorized
    assert not receipt.automatic_replay_authorized
    print("PREPARED", flush=True)
"""


@pytest.mark.parametrize(
    ("variation", "expected"),
    [
        ("same", ("BLOCKED", "PREPARED")),
        ("distinct-observation", ("BLOCKED", "PREPARED")),
        ("distinct-policy", ("PREPARED", "PREPARED")),
        ("distinct-owner", ("PREPARED", "PREPARED")),
    ],
)
def test_process_race_preserves_scope_budget_and_durable_dedup(
    tmp_path, variation, expected,
):
    path = tmp_path / "prepared.sqlite3"
    SyntheticProactiveLedger(path)
    gate = tmp_path / "start"
    owners = ("synthetic-owner", "synthetic-owner")
    revisions = (1, 1)
    observations = ("b" * 64, "b" * 64)
    if variation == "distinct-observation":
        observations = ("b" * 64, "c" * 64)
    elif variation == "distinct-policy":
        revisions = (1, 2)
    elif variation == "distinct-owner":
        owners = ("synthetic-owner", "other-owner")
    workers = [
        subprocess.Popen(
            [
                sys.executable, "-c", _CHILD, str(path), str(gate),
                str(tmp_path / f"ready-{i}"),
                owners[i], str(revisions[i]), observations[i],
            ],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        for i in range(2)
    ]
    try:
        deadline = time.monotonic() + 25
        while not all((tmp_path / f"ready-{i}").exists() for i in range(2)):
            if any(worker.poll() is not None for worker in workers):
                raise AssertionError("proactive worker exited before release")
            if time.monotonic() >= deadline:
                raise AssertionError("proactive workers did not reach release")
            time.sleep(0.02)
        gate.touch()
        answers = [worker.communicate(timeout=35) for worker in workers]
    finally:
        gate.touch()
        for worker in workers:
            if worker.poll() is None:
                worker.kill()
                worker.communicate()
    assert all(worker.returncode == 0 for worker in workers), answers
    assert tuple(sorted(out.strip() for out, _ in answers)) == expected
    expected_count = expected.count("PREPARED")
    assert SyntheticProactiveLedger(path).count() == expected_count
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            """SELECT trigger_id, scope_digest, policy_digest,
                      source_digest, observation_digest
               FROM synthetic_prepared_triggers"""
        ).fetchall()
    assert len(rows) == expected_count
    assert len({row[0] for row in rows}) == expected_count
    assert all(row[0].startswith("trigger_") for row in rows)
    assert all(len(part) == 64 for row in rows for part in row[1:])
