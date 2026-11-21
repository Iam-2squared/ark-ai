"""COMMIT-UNKNOWN result and ledger identity cannot become executable hooks.

Use disposable atomic SQLite fixtures only; tests never dispatch tools.
"""

from __future__ import annotations

import pytest

import ark.agency.disconnected_atomic_unknown_outcome_review as triage
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)


def _review(store):
    return triage.review_atomic_unknown_outcome(
        store,
        genesis_atomic_preaction_witness(),
        AtomicIntentClaim("occ_" + "a" * 64, "bound_" + "b" * 64, "c" * 64),
    )


@pytest.mark.parametrize(
    "field",
    (
        "occurrence_id", "local_state", "before_count", "observed_count",
        "locally_present", "dispatch_authorized", "automatic_replay_authorized",
        "external_effect_verified", "independent_custody_verified",
        "manual_review_required", "__getattribute__", "__getattr__",
    ),
)
def test_result_descriptor_replacement_rejected_before_sqlite_or_callback(
    tmp_path, monkeypatch, field: str,
) -> None:
    def unreviewed(*_args, **_kwargs):
        pytest.fail("unreviewed result hook executed")

    store = DisconnectedAtomicPreactionLedger.create(tmp_path / "atomic.sqlite")
    with monkeypatch.context() as patch:
        if field.startswith("__"):
            patch.setattr(
                triage.AtomicUnknownOutcomeReview, field, unreviewed,
                raising=False,
            )
        else:
            patch.setattr(
                triage.AtomicUnknownOutcomeReview, field, property(unreviewed),
            )
        with pytest.raises(
            triage.AtomicUnknownOutcomeRejected, match="protocol changed",
        ):
            _review(store)


@pytest.mark.parametrize("field", ("__getattribute__", "__getattr__"))
def test_ledger_hook_replacement_does_not_reach_user_callback(
    tmp_path, monkeypatch, field: str,
) -> None:
    def unreviewed(*_args, **_kwargs):
        pytest.fail("unreviewed ledger hook executed")

    store = DisconnectedAtomicPreactionLedger.create(tmp_path / "atomic.sqlite")
    with monkeypatch.context() as patch:
        patch.setattr(
            triage.DisconnectedAtomicPreactionLedger,
            field, unreviewed, raising=False,
        )
        with pytest.raises(
            triage.AtomicUnknownOutcomeRejected, match="protocol changed",
        ):
            _review(store)


def test_healthy_manual_review_survives_identity_checks(tmp_path) -> None:
    store = DisconnectedAtomicPreactionLedger.create(tmp_path / "atomic.sqlite")
    result = _review(store)
    assert result.local_state == "UNCHANGED"
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_effect_verified is False
    assert result.independent_custody_verified is False
    assert result.manual_review_required is True
