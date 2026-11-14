"""Four-step Planner success cannot reuse or rewrite detached READ evidence.

The recovered journal, link and READ review are local synthetic witnesses.
None attests backend dispatch, independent provenance or WRITE permission.
"""

from __future__ import annotations

from dataclasses import replace

import pytest
from test_planner_diamond_independent_read_receipts_run690 import _diamond

from ark.agency.disconnected_planner_success_bundle_review import (
    PlannerReadSuccessBundleRejected,
    review_synthetic_succeeded_read_bundle,
)


@pytest.mark.parametrize(
    "fault",
    (
        "swap_link_only",
        "duplicate_pair",
        "change_step",
        "change_registry",
        "change_link_digest",
        "change_journal_tip",
        "change_action_id",
    ),
)
def test_recovered_diamond_rejects_cross_step_or_mutated_receipt(
    tmp_path, fault,
):
    journal, ids, steps, recovered, evidence, backend = _diamond(tmp_path)
    try:
        first_link, first_review = evidence[0]
        changed = list(evidence)
        if fault == "swap_link_only":
            changed[0] = (evidence[1][0], first_review)
        elif fault == "duplicate_pair":
            changed[1] = evidence[0]
        elif fault == "change_step":
            changed[0] = (replace(first_link, step_id=ids[1]), first_review)
        elif fault == "change_registry":
            changed[0] = (
                replace(first_link, registry_revision="tools_" + "0" * 64),
                first_review,
            )
        elif fault == "change_link_digest":
            changed[0] = (
                first_link, replace(first_review, link_sha256="0" * 64),
            )
        elif fault == "change_journal_tip":
            changed[0] = (
                first_link, replace(first_review, journal_tip_sha256="not-a-digest"),
            )
        elif fault == "change_action_id":
            changed[0] = (
                first_link, replace(first_review, action_request_id="act_" + "0" * 64),
            )
        with pytest.raises(PlannerReadSuccessBundleRejected):
            review_synthetic_succeeded_read_bundle(recovered, steps, tuple(changed))
        assert backend.calls == 0

        # The independent real fixture READ receipt set is still valid.
        valid = review_synthetic_succeeded_read_bundle(
            recovered, steps, evidence[2:] + evidence[:2],
        )
        assert valid.step_ids == ids
        assert valid.write_authorized is False
        assert valid.dispatch_authorized is False
        assert valid.automatic_replay_authorized is False
        assert backend.calls == 0
    finally:
        journal.close()
