"""COMMIT-UNKNOWN remains manual-only after an actual child process exits.

The subprocess can commit a synthetic atomic pre-action row and die without
returning a receipt. Cold triage reports only *local* membership and never
promotes that fact into evidence of an external WRITE or retry authority.
"""

from __future__ import annotations

import os
from multiprocessing import get_context
from pathlib import Path

import pytest

from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
from ark.agency.disconnected_atomic_unknown_outcome_review import (
    review_atomic_unknown_outcome,
)


def _claim(seed: str) -> AtomicIntentClaim:
    return AtomicIntentClaim("occ_" + seed * 64, "bound_" + "b" * 64, "c" * 64)


def _commit_without_receipt(path: str, mode: str) -> None:
    if mode != "unchanged":
        ledger = DisconnectedAtomicPreactionLedger(Path(path))
        claim = _claim("a" if mode == "recorded" else "d")
        ledger.reserve(claim, retained=genesis_atomic_preaction_witness())
    os._exit(0)


@pytest.mark.parametrize(
    ("mode", "expected_state", "expected_present"),
    (
        ("recorded", "LOCALLY_RECORDED", True),
        ("unrelated", "ADVANCED_OTHER", False),
        ("unchanged", "UNCHANGED", False),
    ),
)
def test_unknown_child_commit_cannot_authorize_restart_replay(
    tmp_path: Path, mode: str, expected_state: str, expected_present: bool,
) -> None:
    path = tmp_path / "lost-atomic-preaction.sqlite3"
    DisconnectedAtomicPreactionLedger.create(path)
    retained = genesis_atomic_preaction_witness()
    child = get_context("spawn").Process(
        target=_commit_without_receipt, args=(str(path), mode),
    )
    child.start()
    child.join(timeout=35)
    if child.is_alive():
        child.terminate()
        child.join(timeout=5)
    assert child.exitcode == 0

    for _ in range(2):
        cold = DisconnectedAtomicPreactionLedger(path)
        review = review_atomic_unknown_outcome(cold, retained, _claim("a"))
        assert review.local_state == expected_state
        assert review.locally_present is expected_present
        assert review.before_count == 0
        assert review.observed_count == (0 if mode == "unchanged" else 1)
        assert review.dispatch_authorized is False
        assert review.automatic_replay_authorized is False
        assert review.external_effect_verified is False
        assert review.independent_custody_verified is False
        assert review.manual_review_required is True
