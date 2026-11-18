"""Run970: COMMIT-UNKNOWN triage keeps original descriptor guard vectors.

These tests are disconnected local-only reviews. An untrusted history, even
when locally present, never proves a real effect or permits automatic retry.
"""

from __future__ import annotations

import pytest

from ark.agency import disconnected_atomic_unknown_outcome_review as review
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)


@pytest.mark.parametrize("vector", ("_LEDGER_HOOK_NAMES", "_RESULT_FIELDS"))
@pytest.mark.parametrize("mutation", ("empty", "short", "reversed", "rebuilt"))
def test_rebound_protocol_vectors_rejected_before_ledger_access(
    monkeypatch: pytest.MonkeyPatch, vector: str, mutation: str,
) -> None:
    original = getattr(review, vector)
    changed = {
        "empty": (),
        "short": original[:1],
        "reversed": tuple(reversed(original)),
        "rebuilt": tuple(list(original)),
    }[mutation]
    assert changed is not original
    # Check the guard before interpreting an invalid external carrier or
    # calling a ledger method; the failure cannot be merely a type refusal.
    with monkeypatch.context() as patch:
        patch.setattr(review, vector, changed)
        with pytest.raises(
            review.AtomicUnknownOutcomeRejected, match="protocol changed",
        ):
            review.review_atomic_unknown_outcome(
                object(), object(), object(),
            )


def test_original_vectors_keep_commit_unknown_manual_only(tmp_path) -> None:
    ledger = DisconnectedAtomicPreactionLedger.create(
        tmp_path / "run970_unknown.sqlite",
    )
    before = genesis_atomic_preaction_witness()
    claim = AtomicIntentClaim(
        "occ_" + "a" * 64, "bound_" + "b" * 64, "c" * 64,
    )
    result = review.review_atomic_unknown_outcome(ledger, before, claim)
    assert result.local_state == "UNCHANGED"
    assert result.before_count == result.observed_count == 0
    assert result.locally_present is False
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_effect_verified is False
    assert result.independent_custody_verified is False
    assert result.manual_review_required is True
