"""Independent offline audit writers serialize durable content-minimized rows.

Audit rows are not backend effects, issuer evidence, or permissions to retry.
No child starts a backend; SQLite and process gates live in pytest temp files.
"""

import sqlite3
import subprocess
import sys
import time

import pytest

from ark.agency.audit import SQLiteActionAudit

_CHILD = r"""
import pathlib
import sys
import time

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ToolCall

path = pathlib.Path(sys.argv[1])
gate = pathlib.Path(sys.argv[2])
ready = pathlib.Path(sys.argv[3])
index = sys.argv[4]
audit = SQLiteActionAudit(path, clock_ms=lambda: 2000)
call = ToolCall(
    "offline", "local.write", "synthetic",
    {"fixture": "PRIVATE_PAYLOAD_NEVER_IN_SQLITE", "index": index},
)
ready.touch()
deadline = time.monotonic() + 25
while not gate.exists():
    if time.monotonic() >= deadline:
        sys.exit("start gate timed out")
    time.sleep(0.02)
event = audit.append(call, outcome="synthetic_audit_before_mock")
assert event.request_id == call.request_id
print("AUDITED:" + str(event.event_id) + ":" + event.request_id, flush=True)
"""


@pytest.mark.parametrize("iteration", range(2))
def test_two_process_audit_append_has_ordered_unique_ids_without_raw_arguments(
    tmp_path, iteration,
):
    root = tmp_path / f"audit-{iteration}"
    root.mkdir()
    path = root / "audit.sqlite"
    audit = SQLiteActionAudit(path, clock_ms=lambda: 1000)
    gate = root / "start"
    processes = [
        subprocess.Popen(
            [
                sys.executable, "-c", _CHILD, str(path), str(gate),
                str(root / f"ready-{index}"), str(index),
            ],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        for index in range(2)
    ]
    try:
        deadline = time.monotonic() + 25
        while not all((root / f"ready-{index}").exists() for index in range(2)):
            if any(process.poll() is not None for process in processes):
                raise AssertionError("audit writer exited before common start gate")
            if time.monotonic() >= deadline:
                raise AssertionError("audit writers never reached start gate")
            time.sleep(0.02)
        gate.touch()
        replies = [process.communicate(timeout=35) for process in processes]
    finally:
        gate.touch()
        for process in processes:
            if process.poll() is None:
                process.kill()
                process.communicate()
    assert all(process.returncode == 0 for process in processes), replies
    outputs = [stdout.strip() for stdout, _stderr in replies]
    assert all(message.startswith("AUDITED:") for message in outputs)
    ids = sorted(int(message.split(":")[1]) for message in outputs)
    assert ids == [1, 2]
    records = audit.events(after_event_id=0, limit=10)
    assert [event.event_id for event in records] == [1, 2]
    assert {event.request_id for event in records} == {
        message.split(":")[2] for message in outputs
    }
    assert all(
        event.outcome == "synthetic_audit_before_mock"
        and event.occurred_at_ms == 2000
        for event in records
    )
    with sqlite3.connect(path) as conn:
        assert conn.execute("SELECT COUNT(*) FROM action_events").fetchone() == (2,)
    assert b"PRIVATE_PAYLOAD_NEVER_IN_SQLITE" not in path.read_bytes()
