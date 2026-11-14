"""Separate OS interpreters race a privacy-minimized context replay reservation.

No actual context is disclosed; no consent, export or action is authorized.
A matching local hash cannot identify the winning independent caller.
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
    genesis_offline_context_replay_witness,
)
from ark.personal_context_request_binding import bind_offline_context_request

_PRIVATE = "synthetic-private-string-must-not-be-in-ledger"

_CHILD = """
import hashlib
import sys
from pathlib import Path
from ark.personal_context_offline_preview import (
    OfflineContextFixture, build_offline_context_preview,
)
from ark.personal_context_replay_ledger import (
    DisconnectedContextReplayLedger, OfflineContextReplayRejected,
    genesis_offline_context_replay_witness,
)
from ark.personal_context_request_binding import bind_offline_context_request
db, suffix = sys.argv[1:]
private = "synthetic-private-string-must-not-be-in-ledger"
record = OfflineContextFixture(
    "rec_" + "c" * 32, "a" * 64, "b" * 64, private,
    hashlib.sha256(private.encode()).hexdigest(), 1000,
)
preview = build_offline_context_preview(
    (record,), owner_digest="a" * 64,
    allowed_scope_digests=("b" * 64,), observed_at_ms=100,
)
binding = bind_offline_context_request("ctxreq_" + suffix * 64, preview)
try:
    receipt = DisconnectedContextReplayLedger(Path(db)).reserve(
        binding, retained=genesis_offline_context_replay_witness(),
    )
except OfflineContextReplayRejected:
    sys.exit(4)
if (receipt.context_disclosure_authorized is not False
        or receipt.automatic_replay_authorized is not False):
    sys.exit(8)
"""


def _binding(suffix: str):
    record = OfflineContextFixture(
        "rec_" + "c" * 32, "a" * 64, "b" * 64, _PRIVATE,
        hashlib.sha256(_PRIVATE.encode()).hexdigest(), 1000,
    )
    preview = build_offline_context_preview(
        (record,), owner_digest="a" * 64,
        allowed_scope_digests=("b" * 64,), observed_at_ms=100,
    )
    return bind_offline_context_request("ctxreq_" + suffix * 64, preview)


@pytest.mark.parametrize("same_request", (True, False))
def test_multiprocess_context_reservation_has_one_cas_winner(
    tmp_path: Path, same_request: bool,
) -> None:
    path = tmp_path / "context-competition.sqlite"
    DisconnectedContextReplayLedger(path, create=True)
    requests = ("1", "1" if same_request else "2")
    processes = [
        subprocess.Popen(
            [sys.executable, "-c", _CHILD, str(path), suffix],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
        )
        for suffix in requests
    ]
    output = [process.communicate(timeout=30) for process in processes]
    assert sorted(process.returncode for process in processes) == [0, 4], output

    restarted = DisconnectedContextReplayLedger(path)
    tip = restarted.witness()
    assert tip.count == 1
    assert restarted.verify_retained_prefix(
        genesis_offline_context_replay_witness(),
    ) == tip
    assert _PRIVATE.encode() not in path.read_bytes()
    if same_request:
        with pytest.raises(OfflineContextReplayRejected):
            restarted.reserve(_binding("1"), retained=tip)
    else:
        winner = requests[processes.index(next(
            process for process in processes if process.returncode == 0
        ))]
        loser = "2" if winner == "1" else "1"
        next_receipt = restarted.reserve(_binding(loser), retained=tip)
        assert next_receipt.witness.count == 2
        assert restarted.witness() == next_receipt.witness
        assert _PRIVATE.encode() not in path.read_bytes()
