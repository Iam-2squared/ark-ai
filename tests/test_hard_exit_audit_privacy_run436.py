"""Real child-process termination at local audit and privacy COMMIT boundaries.

SQLite files and identities are disposable fixtures. A committed event/veto
survives a lost Python return; an uncommitted event does not. Neither a local
audit receipt nor an absent revocation marker grants real execution/consent.
"""

import sqlite3
import subprocess
import sys

import pytest

from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ToolCall
from ark.memory import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)

_AUDIT_CHILD = r"""
import os
import pathlib
import sys

import ark.agency.audit as audit_module
from ark.agency.audit import SQLiteActionAudit
from ark.agency.contracts import ToolCall

class BeforeCommit:
    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __enter__(self):
        self.wrapped.__enter__()
        return self

    def __exit__(self, *_args):
        # The SQL INSERT has run, but sqlite3.Connection.__exit__ has not
        # committed. The child disappears with an open writer transaction.
        os._exit(51)

    def __getattr__(self, name):
        return getattr(self.wrapped, name)

path = pathlib.Path(sys.argv[1])
phase = sys.argv[2]
audit = SQLiteActionAudit(path, clock_ms=lambda: 77)
if phase == "before_commit":
    original_connect = audit._connect
    audit._connect = lambda: BeforeCommit(original_connect())
elif phase == "after_commit":
    audit_module.ActionAuditEvent = lambda *_args: os._exit(52)
else:
    sys.exit("invalid audit phase")
call = ToolCall("inert", "fixture.read", "disconnected", {"n": 1})
audit.append(call, outcome="synthetic_pre_action_audit")
sys.exit("audit child unexpectedly returned")
"""

_PRIVACY_CHILD = r"""
import os
import pathlib
import sys

from ark.memory import MemoryScope
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger

class AfterCommit:
    def __init__(self, wrapped):
        self.wrapped = wrapped

    def commit(self):
        self.wrapped.commit()
        os._exit(53)

    def __getattr__(self, name):
        return getattr(self.wrapped, name)

ledger = SyntheticContextRevocationLedger(pathlib.Path(sys.argv[1]))
original_connect = ledger._connect
ledger._connect = lambda *, readonly: AfterCommit(
    original_connect(readonly=readonly)
)
ledger.revoke(MemoryScope("synthetic-owner", "private"), at_ms=100)
sys.exit("revocation child unexpectedly returned")
"""


def _exit_child(code, path, expected, *args):
    finished = subprocess.run(
        [sys.executable, "-c", code, str(path), *args],
        capture_output=True, text=True, timeout=35, check=False,
    )
    assert finished.returncode == expected, (
        finished.returncode, finished.stdout, finished.stderr,
    )


@pytest.mark.parametrize(
    ("phase", "exit_code", "expected_count"),
    [("before_commit", 51, 0), ("after_commit", 52, 1)],
)
def test_audit_hard_exit_preserves_commit_boundary(
    tmp_path, phase, exit_code, expected_count,
):
    path = tmp_path / "audit.sqlite3"
    SQLiteActionAudit(path, clock_ms=lambda: 77)
    _exit_child(_AUDIT_CHILD, path, exit_code, phase)
    recovered = SQLiteActionAudit(path, clock_ms=lambda: 78)
    call = ToolCall("inert", "fixture.read", "disconnected", {"n": 1})
    events = recovered.events()
    assert len(events) == expected_count
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT request_id, outcome FROM action_events"
        ).fetchall()
    assert len(rows) == expected_count
    if expected_count:
        assert rows == [(call.request_id, "synthetic_pre_action_audit")]
        assert events[0].request_id == call.request_id
        assert events[0].outcome == "synthetic_pre_action_audit"
    else:
        # Reuse is possible only because the prior INSERT was not committed;
        # no external action or side effect was ever invoked by this test.
        event = recovered.append(call, outcome="synthetic_pre_action_audit")
        assert event.event_id == 1
        assert len(recovered.events()) == 1


def test_privacy_veto_survives_hard_exit_after_commit(tmp_path):
    path = tmp_path / "revocations.sqlite3"
    _exit_child(_PRIVACY_CHILD, path, 53)
    ledger = SyntheticContextRevocationLedger(path)
    scope = MemoryScope("synthetic-owner", "private")
    with sqlite3.connect(path) as conn:
        rows = conn.execute(
            "SELECT scope_digest, revoked_at_ms FROM synthetic_context_revocations"
        ).fetchall()
    assert len(rows) == 1
    assert len(rows[0][0]) == 64
    assert rows[0][1] == 100
    assert "synthetic-owner" not in rows[0][0]
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        ledger.assert_not_revoked((scope,))
    with pytest.raises(SyntheticContextRevocationRejected, match="already revoked"):
        ledger.revoke(scope, at_ms=101)
