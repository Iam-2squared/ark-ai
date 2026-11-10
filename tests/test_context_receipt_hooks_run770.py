"""Subprocess-isolated post-COMMIT receipt hook substitution regression.

A durable local reservation survives a refused reply. No consent, disclosure,
notification, dispatch or automatic replay is inferred from local SQLite.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_CHILD = r"""
import sqlite3
import sys
from pathlib import Path
import ark.personal_context_replay_ledger as replay
from ark.personal_context_request_binding import OfflineContextRequestBinding

path = Path(sys.argv[1])
hook = sys.argv[2]
ledger = replay.DisconnectedContextReplayLedger(path, create=True)
genesis = replay.genesis_offline_context_replay_witness()
binding = OfflineContextRequestBinding(
    "ctxreq_" + "1" * 64, "a" * 64, "b" * 64, 1, "c" * 64,
)
cls = replay.OfflineContextReplayReceipt
before = vars(cls).get(hook)
calls = []
def trap(*args, **kwargs):
    calls.append(hook)
    raise AssertionError("untrusted receipt hook executed")
setattr(cls, hook, staticmethod(trap) if hook == "__new__" else trap)
try:
    try:
        ledger.reserve(binding, retained=genesis)
    except replay.OfflineContextReplayRejected as exc:
        assert "postcommit" in str(exc)
    else:
        raise AssertionError("untrusted receipt hook unexpectedly accepted")
    assert calls == []
finally:
    if before is None:
        delattr(cls, hook)
    else:
        setattr(cls, hook, before)
with sqlite3.connect(path) as conn:
    assert conn.execute("SELECT COUNT(*) FROM context_requests").fetchone() == (1,)
assert replay.DisconnectedContextReplayLedger(path).witness().count == 1
try:
    ledger.reserve(binding, retained=genesis)
except replay.OfflineContextReplayRejected as exc:
    assert "stale" in str(exc)
else:
    raise AssertionError("same request was blindly replayed")
"""


@pytest.mark.parametrize(
    "hook", ("__new__", "__getattribute__", "__getattr__"),
)
def test_receipt_hooks_rejected_without_execution_after_commit(
    tmp_path: Path, hook: str,
) -> None:
    result = subprocess.run(
        [
            sys.executable, "-c", _CHILD,
            str(tmp_path / "context-replay.sqlite"), hook,
        ],
        capture_output=True, text=True, check=False, timeout=30,
    )
    assert result.returncode == 0, result.stdout + result.stderr
