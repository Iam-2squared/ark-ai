"""Independent local processes cannot double-revoke or regrant a scope.

This is disconnected, content-minimized, disposable SQLite evidence, not a
real user's consent, real deletion, or authorization to disclose context.
"""

import sqlite3
import subprocess
import sys
import time

import pytest

from ark.memory import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)

_CHILD = r"""
import pathlib
import sys
import time

from ark.memory import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)

path = pathlib.Path(sys.argv[1])
gate = pathlib.Path(sys.argv[2])
ready = pathlib.Path(sys.argv[3])
ledger = SyntheticContextRevocationLedger(path)
scope = MemoryScope("private-local-owner", "profile")
ready.touch()
deadline = time.monotonic() + 25
while not gate.exists():
    if time.monotonic() >= deadline:
        sys.exit("start gate timed out")
    time.sleep(0.02)
try:
    digest = ledger.revoke(scope, at_ms=2000)
except SyntheticContextRevocationRejected as error:
    assert "already revoked" in str(error)
    print("ALREADY", flush=True)
else:
    print("REVOKED:" + digest, flush=True)
"""


@pytest.mark.parametrize("iteration", range(2))
def test_disconnected_revocation_has_one_persistent_winner_across_processes(
    tmp_path, iteration,
):
    root = tmp_path / f"revocation-{iteration}"
    root.mkdir()
    path = root / "veto.sqlite"
    ledger = SyntheticContextRevocationLedger(path)
    scope = MemoryScope("private-local-owner", "profile")
    gate = root / "start"
    processes = [
        subprocess.Popen(
            [
                sys.executable, "-c", _CHILD, str(path), str(gate),
                str(root / f"ready-{index}"),
            ],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        for index in range(2)
    ]
    try:
        deadline = time.monotonic() + 25
        while not all((root / f"ready-{index}").exists() for index in range(2)):
            if any(process.poll() is not None for process in processes):
                raise AssertionError("revocation contender exited before start gate")
            if time.monotonic() >= deadline:
                raise AssertionError("revocation contenders never reached start gate")
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
    assert outputs.count("ALREADY") == 1
    winners = [item[8:] for item in outputs if item.startswith("REVOKED:")]
    assert len(winners) == 1
    assert len(winners[0]) == 64
    assert all(char in "0123456789abcdef" for char in winners[0])
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT scope_digest, revoked_at_ms FROM synthetic_context_revocations",
        ).fetchall()
    assert rows == [(winners[0], 2000)]
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        ledger.assert_not_revoked((scope,))
