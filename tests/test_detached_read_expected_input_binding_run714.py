"""Exact synthetic READ input binding against a recovered hash-chain snapshot."""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.agency.disconnected_read_input_binding_review import (
    ReadInputBindingRejected,
    ReadInputBindingReview,
    review_detached_read_input_binding,
)
from ark.agency.disconnected_read_journal import (
    DisconnectedReadJournal,
    ReadJournalSnapshot,
    ReadJournalWitness,
    ReadReceipt,
    _chain,
    genesis_witness,
)
from ark.agency.disconnected_read_recovery_journal_bridge import (
    review_detached_read_journal_recovery,
)
from ark.agency.disconnected_read_recovery_schedule import ReadRecoveryStep

REQUEST = "req_" + "a" * 32
A = "step_" + "1" * 16
B = "step_" + "2" * 16
C = "step_" + "3" * 16
IA, IB, IC = "d" * 64, "e" * 64, "f" * 64
RA, RB, RC = "a" * 64, "b" * 64, "c" * 64


def _steps():
    return (
        ReadRecoveryStep(A, "math.sum", (), "SUCCEEDED", RA),
        ReadRecoveryStep(B, "text.stats", (A,), "SUCCEEDED", RB),
        ReadRecoveryStep(C, "text.find", (B,), "NOT_STARTED"),
    )


def _rows():
    return (
        ReadReceipt(REQUEST, A, "math.sum", IA, RA),
        ReadReceipt(REQUEST, B, "text.stats", IB, RB),
    )


def _snapshot(rows):
    tip = genesis_witness().tip_sha256
    for index, row in enumerate(rows, 1):
        tip = _chain(tip, index, row)
    witness = ReadJournalWitness(len(rows), tip)
    return ReadJournalSnapshot(witness, rows), witness


def test_restarted_sqlite_read_inputs_match_only_retained_plan(tmp_path):
    path = tmp_path / "synthetic-read-inputs.sqlite"
    with DisconnectedReadJournal.create(path) as journal:
        witness = genesis_witness()
        for row in _rows():
            witness = journal.append(row, witness)
    with DisconnectedReadJournal.open(path) as journal:
        snapshot = journal.recover_receipts(witness)
        review = review_detached_read_input_binding(
            REQUEST, _steps(), snapshot, witness, ((A, IA), (B, IB)),
        )
    assert review.successful_step_ids == (A, B)
    assert review.journal_tip_sha256 == witness.tip_sha256
    assert len(review.input_binding_sha256) == 64
    assert review.backend_dispatched is False
    assert review.external_result_proven is False
    assert review.automatic_replay_authorized is False
    assert review.independent_custody_proven is False


def test_valid_rehashed_journal_does_not_prove_expected_input():
    # The original journal join only knows result digests and append order.
    # A locally rewritten receipt with a recomputed tip can pass that join;
    # independent retained expected-input digests must still reject it.
    altered = (replace(_rows()[0], input_digest=IC), _rows()[1])
    snapshot, retained = _snapshot(altered)
    assert review_detached_read_journal_recovery(
        REQUEST, _steps(), snapshot, retained,
    ).successful_step_ids == (A, B)
    with pytest.raises(ReadInputBindingRejected, match="input digest"):
        review_detached_read_input_binding(
            REQUEST, _steps(), snapshot, retained, ((A, IA), (B, IB)),
        )


@pytest.mark.parametrize(
    "claims",
    (
        ((A, IA),),
        ((B, IB), (A, IA)),
        ((A, IA), (A, IA)),
        ((A, IA), (B, IB), (C, IC)),
        ((A, IA), (B, False)),
        ((A, IA), (B, "z" * 64)),
        ((A, IA), [B, IB]),
    ),
)
def test_missing_reordered_duplicate_extra_or_noncanonical_manifest_denied(claims):
    snapshot, witness = _snapshot(_rows())
    with pytest.raises(ReadInputBindingRejected):
        review_detached_read_input_binding(
            REQUEST, _steps(), snapshot, witness, tuple(claims),
        )


def test_unrelated_success_does_not_bind_unknown_branch():
    steps = (
        ReadRecoveryStep(A, "math.sum", (), "UNKNOWN"),
        ReadRecoveryStep(B, "text.stats", (A,), "NOT_STARTED"),
        ReadRecoveryStep(C, "text.find", (), "SUCCEEDED", RC),
    )
    snapshot, witness = _snapshot(
        (ReadReceipt(REQUEST, C, "text.find", IC, RC),),
    )
    review = review_detached_read_input_binding(
        REQUEST, steps, snapshot, witness, ((C, IC),),
    )
    assert review.successful_step_ids == (C,)
    with pytest.raises(ReadInputBindingRejected):
        review_detached_read_input_binding(
            REQUEST, steps, snapshot, witness, ((A, IA), (C, IC)),
        )


def test_replaced_report_constructor_is_rejected_before_execution(monkeypatch):
    snapshot, witness = _snapshot(_rows())
    executed = []
    monkeypatch.setattr(
        ReadInputBindingReview, "__init__",
        lambda *args: executed.append(args),
    )
    with pytest.raises(ReadInputBindingRejected, match="authority changed"):
        review_detached_read_input_binding(
            REQUEST, _steps(), snapshot, witness, ((A, IA), (B, IB)),
        )
    assert executed == []
