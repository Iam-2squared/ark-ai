"""Independent local processes compete for one inert synthetic WRITE reservation.

Only disposable SQLite and mock backends are used. A winning reservation is
not signed issuer approval, external outcome proof or real dispatch authority.
"""

import sqlite3
import subprocess
import sys
import time

import pytest

from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore

_CHILD = r"""
import pathlib
import sys
import time

from ark.agency.contracts import Effect, OneShotAuthorization, ToolCall
from ark.agency.durable_occurrence_review import SyntheticOccurrenceStore, SyntheticReplayRejected
from ark.agency.registry import ToolRegistration, ToolRegistry


class NoDispatch:
    def execute(self, _call):
        raise AssertionError("a synthetic reservation must never execute")


path = pathlib.Path(sys.argv[1])
gate = pathlib.Path(sys.argv[2])
ready = pathlib.Path(sys.argv[3])
token_id = sys.argv[4]
occurrence_id = sys.argv[5]
store = SyntheticOccurrenceStore(path)
call = ToolCall("mock", "write", "fixture", {"value": 1})
registry = ToolRegistry((
    ToolRegistration("mock", "write", Effect.WRITE, "local-mock", NoDispatch()),
))
ready.touch()
deadline = time.monotonic() + 25
while not gate.exists():
    if time.monotonic() >= deadline:
        sys.exit("barrier timed out")
    time.sleep(0.02)
try:
    receipt = store.reserve_synthetic(
        registry,
        call,
        OneShotAuthorization(token_id, call.request_id, 1000),
        occurrence_id=occurrence_id,
        now_ms=20,
    )
except SyntheticReplayRejected as exc:
    if "already reserved" not in str(exc):
        raise
    print("REPLAY", flush=True)
else:
    assert not receipt.dispatch_authorized
    assert not receipt.outcome_known
    assert not receipt.automatic_replay_authorized
    print("SUCCESS", flush=True)
"""


@pytest.mark.parametrize("conflict", ("same-token", "same-occurrence", "both"))
def test_two_process_reservations_have_one_durable_winner(tmp_path, conflict):
    path = tmp_path / "isolated-occurrences.sqlite3"
    SyntheticOccurrenceStore(path)
    gate = tmp_path / "start"
    token_ids = ("fixture-token-a", "fixture-token-b")
    occurrence_ids = ("occ_" + "a" * 64, "occ_" + "b" * 64)
    if conflict in ("same-token", "both"):
        token_ids = (token_ids[0], token_ids[0])
    if conflict in ("same-occurrence", "both"):
        occurrence_ids = (occurrence_ids[0], occurrence_ids[0])
    processes = [
        subprocess.Popen(
            [
                sys.executable, "-c", _CHILD, str(path), str(gate),
                str(tmp_path / f"ready-{index}"),
                token_ids[index], occurrence_ids[index],
            ],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        for index in range(2)
    ]
    try:
        deadline = time.monotonic() + 25
        while not all((tmp_path / f"ready-{index}").exists() for index in range(2)):
            if any(process.poll() is not None for process in processes):
                raise AssertionError("fixture process exited before barrier")
            if time.monotonic() >= deadline:
                raise AssertionError("fixture processes did not reach barrier")
            time.sleep(0.02)
        gate.touch()
        responses = [process.communicate(timeout=35) for process in processes]
    finally:
        gate.touch()
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate()
    assert all(process.returncode == 0 for process in processes), responses
    assert sorted(output.strip() for output, _ in responses) == ["REPLAY", "SUCCESS"]
    restarted = SyntheticOccurrenceStore(path)
    assert restarted.count_synthetic() == 1
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT token_digest, occurrence_id FROM synthetic_occurrence_reservations"
        ).fetchall()
    assert len(rows) == 1
    assert rows[0][0] not in token_ids
    assert len(rows[0][0]) == 64
    assert rows[0][1] in occurrence_ids
