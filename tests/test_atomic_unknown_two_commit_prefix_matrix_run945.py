"""Exact retained-prefix COMMIT-UNKNOWN matrix after two safe local commits.

Synthetic audit and intent rows are not authenticated external outcomes.
No real tool, approval, replay, hardware, payment, or notification is used.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
from ark.agency.disconnected_atomic_unknown_outcome_review import (
    AtomicUnknownOutcomeRejected,
    review_atomic_unknown_outcome,
)


def _claim(letter: str) -> AtomicIntentClaim:
    return AtomicIntentClaim(
        "occ_" + letter * 64, "bound_" + letter * 64, letter * 64,
    )


@pytest.mark.parametrize(
    ("prefix", "which", "expected"),
    (
        ("genesis", "a", "LOCALLY_RECORDED"),
        ("genesis", "b", "LOCALLY_RECORDED"),
        ("genesis", "c", "ADVANCED_OTHER"),
        ("first", "a", "PREEXISTING"),
        ("first", "b", "LOCALLY_RECORDED"),
        ("first", "c", "ADVANCED_OTHER"),
        ("second", "a", "PREEXISTING"),
        ("second", "b", "PREEXISTING"),
        ("second", "c", "UNCHANGED"),
    ),
)
def test_two_commit_local_triage_never_authorizes_unknown_write(
    tmp_path, prefix: str, which: str, expected: str,
) -> None:
    path = tmp_path / "synthetic-audit-intent.sqlite3"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    genesis = genesis_atomic_preaction_witness()
    first = ledger.reserve(_claim("a"), retained=genesis)
    second = ledger.reserve(_claim("b"), retained=first)
    before = {"genesis": genesis, "first": first, "second": second}[prefix]

    for _ in range(2):
        # Read a new connection each time: a preexisting local membership
        # may never be interpreted as a known external effect.
        review = review_atomic_unknown_outcome(
            DisconnectedAtomicPreactionLedger(path), before, _claim(which),
        )
        assert review.local_state == expected
        assert review.before_count == before.count
        assert review.observed_count == 2
        assert review.locally_present is (which in "ab")
        assert review.dispatch_authorized is False
        assert review.automatic_replay_authorized is False
        assert review.external_effect_verified is False
        assert review.independent_custody_verified is False
        assert review.manual_review_required is True


@pytest.mark.parametrize("where", ("genesis", "first", "second"))
def test_changed_retained_tip_refused_without_mutating_real_history(
    tmp_path, where: str,
) -> None:
    path = tmp_path / "synthetic-retained-prefix.sqlite3"
    ledger = DisconnectedAtomicPreactionLedger.create(path)
    genesis = genesis_atomic_preaction_witness()
    first = ledger.reserve(_claim("a"), retained=genesis)
    second = ledger.reserve(_claim("b"), retained=first)
    before = {"genesis": genesis, "first": first, "second": second}[where]
    forged = replace(before, tip_sha256="0" * 64)

    with pytest.raises(AtomicUnknownOutcomeRejected):
        review_atomic_unknown_outcome(
            DisconnectedAtomicPreactionLedger(path), forged, _claim("a"),
        )
    unchanged = ledger.inspect(second)
    assert unchanged.witness == second
    assert unchanged.occurrence_ids == (_claim("a").occurrence_id, _claim("b").occurrence_id)
