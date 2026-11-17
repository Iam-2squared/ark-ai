"""Run948: three independent SQLite reviews cannot jointly grant private dispatch.

The Planner, pre-action, Memory and revocation files are synthetic and local.
Their sequential observations are NOT a cross-store snapshot or authorization.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import PlanStep, StepState, ToolCall
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    DisconnectedAtomicPreactionLedger,
    genesis_atomic_preaction_witness,
)
from ark.agency.disconnected_atomic_unknown_outcome_review import (
    review_atomic_unknown_outcome,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.personal_context_retention_review import review_synthetic_retention_inventory
from ark.personal_context_revocation_continuity_review import (
    review_revocation_continuity,
)
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)


@pytest.mark.parametrize("order", ("privacy-first", "planner-first", "preaction-first"))
def test_cold_unknown_plan_and_preaction_do_not_override_privacy_veto(
    tmp_path, order: str,
) -> None:
    scope = MemoryScope("synthetic-owner", "private")
    other = MemoryScope("synthetic-owner", "public")
    memory_path = tmp_path / "private-memory.sqlite3"
    memory = SQLiteMemoryStore(memory_path, clock_ms=lambda: 100)
    memory.put(MemoryWrite(scope, "source", "SYNTHETIC_PRIVATE_SENTINEL"))
    memory.put(MemoryWrite(other, "source", "PUBLIC_FIXTURE"))
    revocation_path = tmp_path / "privacy-veto.sqlite3"
    revocations = SyntheticContextRevocationLedger(revocation_path)
    retained_veto = review_revocation_continuity(revocations)

    planner_path = tmp_path / "plan.sqlite3"
    steps = (PlanStep(
        "offline-step",
        ToolCall("fixture.offline", "fixture.write", "private", {"id": 1}),
    ),)
    journal = SyntheticPlanJournal(planner_path, steps)
    retained_plan = journal.recover().tail

    audit_path = tmp_path / "preaction.sqlite3"
    DisconnectedAtomicPreactionLedger.create(audit_path)
    retained_preaction = genesis_atomic_preaction_witness()
    claim = AtomicIntentClaim("occ_" + "a" * 64, "bound_" + "b" * 64, "c" * 64)

    def record_planner() -> None:
        receipt = SyntheticPlanJournal(planner_path, steps).append(
            "offline-step", StepState.RUNNING, expected_revision=0,
            at_ms=180, retained=retained_plan,
        )
        assert receipt.dispatch_authorized is False
        assert receipt.automatic_replay_authorized is False

    def record_preaction() -> None:
        DisconnectedAtomicPreactionLedger(audit_path).reserve(
            claim, retained=retained_preaction,
        )

    if order == "privacy-first":
        revocations.revoke(scope, at_ms=150)
        record_planner()
        record_preaction()
    elif order == "planner-first":
        record_planner()
        record_preaction()
        revocations.revoke(scope, at_ms=150)
    else:
        record_preaction()
        revocations.revoke(scope, at_ms=150)
        record_planner()

    # Cold readbacks deliberately observe three distinct store epochs.
    plan = SyntheticPlanJournal(planner_path, steps).recover(
        retained=retained_plan,
    )
    unknown = review_atomic_unknown_outcome(
        DisconnectedAtomicPreactionLedger(audit_path),
        retained_preaction, claim,
    )
    private = review_synthetic_retention_inventory(
        SQLiteMemoryStore(memory_path, clock_ms=lambda: 250),
        scope,
        SyntheticContextRevocationLedger(revocation_path, require_existing=True),
        now_ms=250, retained_revocations=retained_veto,
    )

    assert plan.ambiguous_running_steps == ("offline-step",)
    assert plan.dispatch_authorized is False
    assert plan.automatic_replay_authorized is False
    assert unknown.local_state == "LOCALLY_RECORDED"
    assert unknown.locally_present is True
    assert unknown.manual_review_required is True
    assert unknown.dispatch_authorized is False
    assert unknown.automatic_replay_authorized is False
    assert unknown.external_effect_verified is False
    assert unknown.independent_custody_verified is False
    assert private.revoked is True
    assert private.context_use_authorized is False
    assert private.deletion_authorized is False
    assert private.erasure_completed is False
    with pytest.raises(SyntheticContextRevocationRejected):
        SyntheticContextRevocationLedger(
            revocation_path, require_existing=True,
        ).assert_not_revoked((scope,))
    for review in (plan, unknown, private):
        assert "SYNTHETIC_PRIVATE_SENTINEL" not in repr(review)
