"""Detached READ recovery rejects substituted snapshot classes before SQLite access.

Each reflective mutation lives in a fresh interpreter to avoid inherited
CPython special-method slot contamination of unrelated tests. Only synthetic
local journal fixtures are used, never actual tool execution.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

_SCRIPT = """
import sys
from pathlib import Path

from ark.agency.disconnected_read_journal import (
    DisconnectedReadJournal,
    ReadJournalRejected,
    ReadJournalSnapshot,
    genesis_witness,
)

path = Path(sys.argv[2])
ledger = DisconnectedReadJournal.create(path)
retained = genesis_witness()
healthy = ledger.recover_receipts(retained)
assert healthy.receipts == ()
assert healthy.dispatch_authorized is False
assert healthy.automatic_replay_authorized is False
ledger.close()

def hostile(*args, **kwargs):
    raise AssertionError("hostile callback executed")

kind = sys.argv[1]
if kind == "init":
    ReadJournalSnapshot.__init__ = hostile
elif kind == "new":
    ReadJournalSnapshot.__new__ = staticmethod(hostile)
elif kind == "slot":
    ReadJournalSnapshot.witness = property(hostile)
elif kind == "lookup":
    ReadJournalSnapshot.__getattribute__ = hostile
elif kind == "denial":
    ReadJournalSnapshot.dispatch_authorized = property(hostile)
else:
    raise AssertionError("unexpected fixture")

try:
    ledger.recover_receipts(retained)  # closed handle; early refusal is required
except ReadJournalRejected as exc:
    assert "snapshot constructor changed" in str(exc)
else:
    raise AssertionError("modified result class was accepted")
"""


@pytest.mark.parametrize("kind", ("init", "new", "slot", "lookup", "denial"))
def test_snapshot_class_mutation_is_refused_before_closed_handle_access(
    tmp_path, kind,
):
    run = subprocess.run(
        [
            sys.executable, "-c", _SCRIPT,
            kind, str(tmp_path / f"{kind}-read.sqlite"),
        ],
        capture_output=True, text=True, check=False, timeout=30,
    )
    assert run.returncode == 0, run.stderr
