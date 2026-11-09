"""Opt-in READ binding must reject substituted carrier getters before access.

All inputs are offline synthetic receipts. No backend action or permission
is granted by a successful read-only reconciliation.
"""

from __future__ import annotations

import pytest
from test_detached_read_input_dependency_custody_run715 import _case

import ark.agency.disconnected_read_input_binding_review as binding
from ark.agency.disconnected_read_journal import (
    ReadJournalSnapshot,
    ReadJournalWitness,
    ReadReceipt,
)
from ark.agency.disconnected_read_recovery_journal_bridge import (
    ReadRecoveryJournalReview,
)


@pytest.mark.parametrize(
    "carrier",
    (
        ReadJournalSnapshot,
        ReadJournalWitness,
        ReadReceipt,
        ReadRecoveryJournalReview,
    ),
)
def test_replaced_input_or_bridge_getter_denied_before_execution(
    monkeypatch, carrier,
):
    inputs = _case()
    callbacks = []

    def poison(self, name):
        callbacks.append((self, name))
        raise AssertionError("untrusted read carrier getter executed")

    monkeypatch.setattr(carrier, "__getattribute__", poison)
    with pytest.raises(
        binding.ReadInputBindingRejected, match="carrier contract changed",
    ):
        binding.review_detached_read_input_binding(*inputs)
    assert callbacks == []


def test_valid_read_reconciliation_keeps_exact_expected_digest_and_denials():
    request, steps, snapshot, retained, expected = _case()
    result = binding.review_detached_read_input_binding(
        request, steps, snapshot, retained, expected,
    )
    assert result.request_id is request
    assert result.successful_step_ids == (expected[0][0],)
    assert result.journal_tip_sha256 == retained.tip_sha256
    assert len(result.input_binding_sha256) == 64
    assert result.backend_dispatched is False
    assert result.external_result_proven is False
    assert result.automatic_replay_authorized is False
    assert result.independent_custody_proven is False
