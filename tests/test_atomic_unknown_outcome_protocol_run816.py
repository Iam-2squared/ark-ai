"""Atomic COMMIT-UNKNOWN reviewer pins local read/decision dependencies.

All cases are disconnected SQLite fixtures; none authorize dispatch or replay.
"""

from __future__ import annotations

import pytest

import ark.agency.disconnected_atomic_unknown_outcome_review as review
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)


def _attempt(tmp_path):
    ledger = DisconnectedAtomicPreactionLedger.create(tmp_path / "intent.sqlite")
    return review.review_atomic_unknown_outcome(
        ledger,
        genesis_atomic_preaction_witness(),
        AtomicIntentClaim("occ_" + "a" * 64, "bound_" + "b" * 64, "c" * 64),
    )


@pytest.mark.parametrize(
    "rebound", ("review_sqlite", "ledger_sqlite", "decision_states"),
)
def test_rebound_history_or_outcome_protocol_refused_before_sqlite(
    tmp_path, monkeypatch, rebound,
):
    with monkeypatch.context() as patch:
        if rebound == "review_sqlite":
            patch.setattr(review, "sqlite3", object())
        elif rebound == "ledger_sqlite":
            patch.setattr(review.ledger_module, "sqlite3", object())
        else:
            patch.setattr(review, "_RESULT_STATES", ("UNCHANGED",))
        with pytest.raises(
            review.AtomicUnknownOutcomeRejected, match="protocol changed",
        ):
            _attempt(tmp_path)


def test_unmodified_protocol_remains_non_authorizing(tmp_path):
    result = _attempt(tmp_path)
    assert result.local_state == "UNCHANGED"
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_effect_verified is False
    assert result.independent_custody_verified is False
    assert result.manual_review_required is True
