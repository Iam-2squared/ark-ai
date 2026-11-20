"""Run1012: process-level CAS for Personal Context replay reservations.

Only deterministic fixture identities and disposable local SQLite are used.
A replay reservation is never disclosure, consent, or Tool dispatch authority.
"""

from __future__ import annotations

import hashlib
import sqlite3
import subprocess
import sys
import time
from pathlib import Path

import pytest

from ark.personal_context_offline_preview import (
    OfflineContextFixture,
    build_offline_context_preview,
)
import ark.personal_context_replay_ledger as replay
from ark.personal_context_request_binding import (
    bind_offline_context_request,
)


_OWNER = "a" * 64
_SCOPE = "b" * 64
_RECORD = "rec_" + "c" * 32
_REQUEST = "ctxreq_" + "d" * 64
_PAYLOAD = "synthetic-only-private-context"


def _binding():
    return _binding_for(_REQUEST)


def _binding_for(request_id: str):
    item = OfflineContextFixture(
        _RECORD,
        _OWNER,
        _SCOPE,
        _PAYLOAD,
        hashlib.sha256(_PAYLOAD.encode("utf-8")).hexdigest(),
        1000,
    )
    preview = build_offline_context_preview(
        (item,),
        owner_digest=_OWNER,
        allowed_scope_digests=(_SCOPE,),
        observed_at_ms=100,
    )
    return bind_offline_context_request(request_id, preview)


_CHILD = """
import sys
import time
from pathlib import Path
import hashlib
from ark.personal_context_offline_preview import (
    OfflineContextFixture, build_offline_context_preview,
)
from ark.personal_context_replay_ledger import (
    DisconnectedContextReplayLedger, OfflineContextReplayRejected,
)
from ark.personal_context_request_binding import bind_offline_context_request

database, ready_name, release_name = sys.argv[1:]
owner = "a" * 64
scope = "b" * 64
record = "rec_" + "c" * 32
request_id = "ctxreq_" + "d" * 64
payload = "synthetic-only-private-context"
item = OfflineContextFixture(
    record, owner, scope, payload,
    hashlib.sha256(payload.encode("utf-8")).hexdigest(), 1000,
)
preview = build_offline_context_preview(
    (item,), owner_digest=owner, allowed_scope_digests=(scope,),
    observed_at_ms=100,
)
binding = bind_offline_context_request(request_id, preview)
ledger = DisconnectedContextReplayLedger(Path(database))
retained = ledger.witness()
ready = Path(ready_name)
release = Path(release_name)
ready.touch()
deadline = time.monotonic() + 25
while not release.exists():
    if time.monotonic() >= deadline:
        sys.exit(8)
    time.sleep(0.01)
try:
    receipt = ledger.reserve(binding, retained=retained)
except OfflineContextReplayRejected:
    sys.exit(4)
assert receipt.request_id == request_id
assert receipt.consent_verified is False
assert receipt.revocation_freshness_verified is False
assert receipt.context_disclosure_authorized is False
assert receipt.tool_dispatch_authorized is False
assert receipt.automatic_replay_authorized is False
sys.exit(0)
"""


def test_two_processes_reserve_one_context_request_at_most_once(
    tmp_path: Path,
) -> None:
    path = tmp_path / "context-replay-multiprocess.sqlite3"
    ledger = replay.DisconnectedContextReplayLedger(path, create=True)
    retained = ledger.witness()
    assert retained.count == 0

    release = tmp_path / "release"
    ready = (tmp_path / "ready-a", tmp_path / "ready-b")
    processes = [
        subprocess.Popen(
            [
                sys.executable, "-c", _CHILD, str(path), str(ready[index]),
                str(release),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        for index in range(2)
    ]
    try:
        deadline = time.monotonic() + 25
        while not all(marker.exists() for marker in ready):
            if any(process.poll() is not None for process in processes):
                outputs = [process.communicate(timeout=5) for process in processes]
                raise AssertionError(f"replay worker exited before barrier: {outputs}")
            if time.monotonic() >= deadline:
                raise AssertionError("replay workers did not reach barrier")
            time.sleep(0.01)
        release.touch()
        outputs = [process.communicate(timeout=35) for process in processes]
        assert sorted(process.returncode for process in processes) == [0, 4], outputs
    finally:
        release.touch()
        for process in processes:
            if process.poll() is None:
                process.terminate()
                process.wait(timeout=5)

    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT COUNT(*),MIN(seq),MAX(seq) FROM context_requests"
        ).fetchone()
        assert conn.execute("PRAGMA quick_check").fetchone() == ("ok",)
    assert rows == (1, 1, 1)
    assert _PAYLOAD.encode("utf-8") not in path.read_bytes()

    cold = replay.DisconnectedContextReplayLedger(path)
    observed = cold.witness()
    assert observed.count == 1
    assert observed.independent_custody_proven is False
    with pytest.raises(replay.OfflineContextReplayRejected, match="stale"):
        cold.reserve(_binding(), retained=retained)
    assert cold.witness() == observed
