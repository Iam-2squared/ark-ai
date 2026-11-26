"""Run1283: context replay reservation survives process exit after native COMMIT.

Synthetic local SQLite only. This is not consent, disclosure, trusted-time,
independent-custody, fsync/power-loss, or exactly-once external-effect evidence.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import pytest

from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    build_offline_context_preview,
)
from ark.personal_context_replay_ledger import (
    DisconnectedContextReplayLedger,
    OfflineContextReplayRejected,
)
from ark.personal_context_request_binding import bind_offline_context_request

_PRIVATE = "run1283-private-context-must-not-be-persisted"

_CHILD = r"""
import hashlib
import os
import sys
from pathlib import Path

import ark.personal_context_replay_ledger as module
from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    build_offline_context_preview,
)
from ark.personal_context_replay_ledger import DisconnectedContextReplayLedger
from ark.personal_context_request_binding import bind_offline_context_request

path = Path(sys.argv[1])
private = "run1283-private-context-must-not-be-persisted"
record = OfflineContextFixture(
    "rec_" + "c" * 32,
    "a" * 64,
    "b" * 64,
    private,
    hashlib.sha256(private.encode("utf-8")).hexdigest(),
    1000,
)
preview = build_offline_context_preview(
    (record,),
    owner_digest="a" * 64,
    allowed_scope_digests=("b" * 64,),
    observed_at_ms=100,
)
binding = bind_offline_context_request("ctxreq_" + "1" * 64, preview)
ledger = DisconnectedContextReplayLedger(path)
retained = ledger.witness()
native_connect = module._ORIGINAL_SQLITE_CONNECT
target_uri = path.resolve().as_uri() + "?mode=rw"


class ExitAfterCommit:
    def __init__(self, connection):
        self.connection = connection

    def commit(self):
        self.connection.commit()
        # Native SQLite COMMIT returned; reserve() has not returned its receipt.
        os._exit(78)

    def __getattr__(self, name):
        return getattr(self.connection, name)


def controlled_connect(*args, **kwargs):
    database = args[0] if args else kwargs.get("database")
    connection = native_connect(*args, **kwargs)
    if database == target_uri:
        return ExitAfterCommit(connection)
    return connection


# Keep sqlite3.connect untouched. The replay module's pinned connector helper
# is replaced together with its expected identity only in this disposable
# child, allowing the test to stop at the native COMMIT boundary.
module._connect_original = controlled_connect
module._ORIGINAL_CONNECT_HELPER = controlled_connect

ledger.reserve(binding, retained=retained)
os._exit(79)
"""


def _binding():
    record = OfflineContextFixture(
        "rec_" + "c" * 32,
        "a" * 64,
        "b" * 64,
        _PRIVATE,
        hashlib.sha256(_PRIVATE.encode("utf-8")).hexdigest(),
        1000,
    )
    preview = build_offline_context_preview(
        (record,),
        owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,),
        observed_at_ms=100,
    )
    return bind_offline_context_request("ctxreq_" + "1" * 64, preview)


def _assert_private_absent(path: Path) -> None:
    for artifact in (
        path,
        path.with_name(path.name + "-wal"),
        path.with_name(path.name + "-shm"),
        path.with_name(path.name + "-journal"),
    ):
        if artifact.exists():
            assert _PRIVATE.encode("utf-8") not in artifact.read_bytes()


def test_native_commit_hard_exit_preserves_one_private_replay_reservation_run1283(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context-replay-native-commit-hard-exit.sqlite3"
    initial = DisconnectedContextReplayLedger(path, create=True)
    genesis = initial.witness()
    assert genesis.count == 0

    child = subprocess.run(
        [sys.executable, "-c", _CHILD, str(path)],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert child.returncode == 78, child.stdout + child.stderr

    cold = DisconnectedContextReplayLedger(path)
    recovered = cold.witness()
    assert recovered.count == 1
    assert recovered.independent_custody_proven is False
    assert cold.verify_retained_prefix(genesis) == recovered
    _assert_private_absent(path)

    with pytest.raises(OfflineContextReplayRejected, match="duplicate context request"):
        cold.reserve(_binding(), retained=recovered)
    assert cold.witness() == recovered
    assert cold.verify_retained_prefix(genesis) == recovered
    _assert_private_absent(path)
