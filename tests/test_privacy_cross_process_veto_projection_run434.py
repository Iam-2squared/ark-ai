"""Independent-process revocation must veto an in-flight private projection.

Only disposable SQLite and local child Python interpreters are exercised.
This is a deny-only synthetic privacy race, never authenticated consent,
erasure, disclosure, a notification, or external Tool execution.
"""

import subprocess
import sys

import pytest

import ark.personal_context_revocation_review as module
from ark.memory.coherent_snapshot_review import CoherentSnapshotRequest
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore
from ark.personal_context_review import ContextSelectionPolicy
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)

_CHILD = r"""
import pathlib
import sys

from ark.memory import MemoryScope
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger

path = pathlib.Path(sys.argv[1])
namespace = sys.argv[2]
ledger = SyntheticContextRevocationLedger(path)
digest = ledger.revoke(MemoryScope("local-owner", namespace), at_ms=150)
assert len(digest) == 64
print("VETO_COMMITTED", flush=True)
"""


def _fixture(tmp_path):
    memory = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    for namespace in ("alpha", "beta"):
        scope = MemoryScope("local-owner", namespace)
        memory.put(MemoryWrite(
            scope, "test-local", "SECRET-FIXTURE-" + namespace,
        ))
    veto = SyntheticContextRevocationLedger(tmp_path / "veto.sqlite")
    request = CoherentSnapshotRequest(
        "local-owner", ("alpha", "beta"), per_namespace_limit=5,
    )
    policy = ContextSelectionPolicy(total_limit=5, per_namespace_limit=5)
    return memory, veto, request, policy


def _revoke_in_child(veto, namespace):
    result = subprocess.run(
        [sys.executable, "-c", _CHILD, str(veto.path), namespace],
        capture_output=True, text=True, timeout=35, check=True,
    )
    assert result.stdout.strip() == "VETO_COMMITTED"


@pytest.mark.parametrize("namespace", ("alpha", "beta"))
def test_other_process_veto_during_memory_projection_is_fail_closed(
    tmp_path, monkeypatch, namespace,
):
    memory, veto, request, policy = _fixture(tmp_path)
    native = module.review_coherent_snapshot
    callbacks = []

    def snapshot_then_revoke(*args, **kwargs):
        snapshot = native(*args, **kwargs)
        _revoke_in_child(veto, namespace)
        callbacks.append(True)
        return snapshot

    monkeypatch.setattr(module, "review_coherent_snapshot", snapshot_then_revoke)
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        module.review_fresh_nonrevoked_context(memory, request, policy, veto)
    assert callbacks == [True]
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        module.review_fresh_nonrevoked_context(memory, request, policy, veto)


@pytest.mark.parametrize("namespace", ("alpha", "beta"))
def test_other_process_veto_after_first_clearance_is_fail_closed(
    tmp_path, monkeypatch, namespace,
):
    memory, veto, request, policy = _fixture(tmp_path)
    native = veto.assert_not_revoked
    attempts = []
    clearances = []

    def check_then_revoke(scopes):
        attempts.append(True)
        # A failing second veto raises *before* another successful clearance.
        native(scopes)
        clearances.append(True)
        if len(clearances) == 1:
            _revoke_in_child(veto, namespace)

    monkeypatch.setattr(veto, "assert_not_revoked", check_then_revoke)
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        module.review_fresh_nonrevoked_context(memory, request, policy, veto)
    assert attempts == [True, True]
    assert clearances == [True]


def test_original_revocation_witness_survives_independent_restart(tmp_path):
    memory, veto, request, policy = _fixture(tmp_path)
    from ark.personal_context_revocation_continuity_review import (
        review_revocation_continuity,
    )

    initial = review_revocation_continuity(veto)
    result = module.review_fresh_nonrevoked_context(
        memory, request, policy, veto, retained_revocations=initial,
    )
    assert result.items
    assert result.dispatch_authorized is False
    assert result.action_authorized is False

    _revoke_in_child(veto, "beta")
    reopened = SyntheticContextRevocationLedger(veto.path)
    latest = review_revocation_continuity(reopened, retained=initial)
    assert len(latest.rows) == len(initial.rows) + 1
    with pytest.raises(SyntheticContextRevocationRejected, match="revoked"):
        module.review_fresh_nonrevoked_context(
            memory, request, policy, reopened, retained_revocations=initial,
        )
