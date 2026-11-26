"""A forged serializer, digest, or recovery bridge cannot inspect READ inputs.

All receipts are synthetic and never execute a backend. The original
dependencies must be restored before processing retained request material.
"""

from __future__ import annotations

import pytest

import ark.agency.disconnected_read_input_binding_review as review_mod
from ark.agency.disconnected_read_journal import (
    ReadJournalSnapshot,
    ReadJournalWitness,
    ReadReceipt,
    _chain,
    genesis_witness,
)
from ark.agency.disconnected_read_recovery_schedule import ReadRecoveryStep

REQUEST = "req_" + "a" * 32
STEP = "step_" + "1" * 16
INPUT = "b" * 64
RESULT = "c" * 64


def _case():
    receipt = ReadReceipt(REQUEST, STEP, "math.sum", INPUT, RESULT)
    tip = _chain(genesis_witness().tip_sha256, 1, receipt)
    witness = ReadJournalWitness(1, tip)
    return (
        REQUEST,
        (ReadRecoveryStep(STEP, "math.sum", (), "SUCCEEDED", RESULT),),
        ReadJournalSnapshot(witness, (receipt,)),
        witness,
        ((STEP, INPUT),),
    )


@pytest.mark.parametrize("dependency", ("sha256", "json.dumps", "recovery"))
def test_replaced_dependency_is_denied_before_poison_callback(
    monkeypatch, dependency,
):
    # Construct the synthetic receipt BEFORE monkeypatching shared SHA/JSON
    # dependencies. Otherwise fixture setup, not the guarded API, executes
    # the poison callback inside the journal's _chain() implementation.
    evidence = _case()
    executed = []

    def poisoned(*args, **kwargs):
        executed.append((args, kwargs))
        raise AssertionError("poisoned dependency must not execute")

    if dependency == "sha256":
        monkeypatch.setattr(review_mod.hashlib, "sha256", poisoned)
    elif dependency == "json.dumps":
        monkeypatch.setattr(review_mod.json, "dumps", poisoned)
    else:
        monkeypatch.setattr(
            review_mod, "review_detached_read_journal_recovery", poisoned,
        )
    with pytest.raises(review_mod.ReadInputBindingRejected, match="authority changed"):
        review_mod.review_detached_read_input_binding(*evidence)
    assert executed == []


def test_original_read_input_dependencies_produce_denial_only_receipt():
    report = review_mod.review_detached_read_input_binding(*_case())
    assert report.successful_step_ids == (STEP,)
    assert len(report.input_binding_sha256) == 64
    assert report.backend_dispatched is False
    assert report.external_result_proven is False
    assert report.automatic_replay_authorized is False
    assert report.independent_custody_proven is False
