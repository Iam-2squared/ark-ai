"""READ journal recovery must reject hostile retained-witness descriptors preaccess.

Subprocess isolation prevents CPython special-method slot mutations from
contaminating unrelated tests. All receipts and paths are local synthetic
fixtures; neither journal recovery nor its denial authorizes tool execution.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

_SCRIPT = """
import sys
from pathlib import Path

import ark.agency.disconnected_read_journal as read

path = Path(sys.argv[2])
journal = read.DisconnectedReadJournal.create(path)
retained = read.genesis_witness()
snapshot = journal.recover_receipts(retained)
assert snapshot.receipts == ()
assert snapshot.dispatch_authorized is False
assert snapshot.automatic_replay_authorized is False
journal.close()

visited = []

def hostile(*args, **kwargs):
    visited.append("untrusted witness descriptor executed")
    raise AssertionError("retained witness read before carrier integrity check")

kind = sys.argv[1]
if kind == "count":
    read.ReadJournalWitness.count = property(hostile)
elif kind == "tip_sha256":
    read.ReadJournalWitness.tip_sha256 = property(hostile)
elif kind == "lookup":
    read.ReadJournalWitness.__getattribute__ = hostile
elif kind == "new":
    read.ReadJournalWitness.__new__ = staticmethod(hostile)
elif kind == "denial":
    read.ReadJournalWitness.dispatch_authorized = property(hostile)
else:
    raise AssertionError("unexpected hostile fixture")

try:
    journal.recover_receipts(retained)
except read.ReadJournalRejected as exc:
    assert "invalid retained witness" in str(exc), str(exc)
else:
    raise AssertionError("mutated retained witness was accepted")
assert visited == []
"""


@pytest.mark.parametrize(
    "kind", ("count", "tip_sha256", "lookup", "new", "denial"),
)
def test_hostile_retained_witness_rejected_before_any_getter_or_sqlite(
    tmp_path, kind,
):
    run = subprocess.run(
        [
            sys.executable, "-c", _SCRIPT,
            kind, str(tmp_path / f"{kind}-journal.sqlite"),
        ],
        capture_output=True, text=True, check=False, timeout=30,
    )
    assert run.returncode == 0, run.stderr
