"""Atomic batch reader admission constants cannot change mid-process.

All requests are disconnected synthetic WRITEs; no token or tool execution.
"""
from __future__ import annotations

import re

import pytest

import ark.agency.disconnected_atomic_batch_binding_snapshot_review as batch
from ark.agency.contracts import Effect, ToolCall
from ark.agency.disconnected_atomic_binding_snapshot_review import (
    AtomicBindingSnapshotRejected,
)
from ark.agency.disconnected_atomic_preaction_ledger import (
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
from ark.agency.registry import ToolRegistration, ToolRegistry


class InertBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("disconnected batch must never dispatch")


@pytest.mark.parametrize(
    ("name", "replacement"),
    (
        ("_MAX_BATCH", 33),
        ("_MAX_BATCH", 0),
        ("_MAX_BATCH", True),
        ("_MAX_BATCH", -1),
        ("_OCCURRENCE", re.compile(".*")),
        ("_LOCAL_STATES", ("ABSENT", "LOCAL_MATCH")),
    ),
)
def test_batch_boundaries_cannot_be_replaced_before_registry_read(
    tmp_path, monkeypatch, name, replacement,
):
    backend = InertBackend()
    registry = ToolRegistry((
        ToolRegistration("writer", "synthetic.write", Effect.WRITE, "mock", backend),
    ))
    ledger = DisconnectedAtomicPreactionLedger.create(tmp_path / "batch.sqlite")
    witness = genesis_atomic_preaction_witness()
    requests = ((
        "occ_" + "a" * 64,
        ToolCall("writer", "synthetic.write", "fixture"),
    ),)
    with monkeypatch.context() as patch:
        patch.setattr(batch, name, replacement)
        with pytest.raises(
            AtomicBindingSnapshotRejected, match="reader definition changed",
        ):
            batch.review_registered_atomic_binding_batch_snapshot(
                ledger, witness, registry, requests,
            )
    # Restoring the original module contract returns a manual-only local
    # ABSENT observation, never a grant or permission to replay the WRITE.
    result = batch.review_registered_atomic_binding_batch_snapshot(
        ledger, witness, registry, requests,
    )
    assert result.local_states == (("occ_" + "a" * 64, "ABSENT"),)
    assert result.retained_count == 0
    assert result.tool_dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.manual_review_required is True
    assert backend.calls == 0
