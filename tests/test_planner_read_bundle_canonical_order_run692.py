"""Recovered Planner READ-bundle receipts are canonically order independent.

The same closed succeeded DAG must produce a single local synthetic digest,
regardless of caller receipt ordering, while never permitting WRITE, dispatch,
external execution attribution, or automatic replay.
"""

from __future__ import annotations

from itertools import permutations

import pytest
from test_planner_diamond_independent_read_receipts_run690 import _diamond

from ark.agency.disconnected_planner_success_bundle_review import (
    PlannerReadSuccessBundleRejected,
    review_synthetic_succeeded_read_bundle,
)


@pytest.mark.parametrize("order", tuple(permutations(range(4))))
def test_succeeded_diamond_canonical_bundle_digest_independent_of_order(
    tmp_path, order,
):
    journal, ids, steps, recovered, evidence, backend = _diamond(tmp_path)
    try:
        canonical = review_synthetic_succeeded_read_bundle(
            recovered, steps, evidence,
        )
        shuffled = review_synthetic_succeeded_read_bundle(
            recovered, steps, tuple(evidence[index] for index in order),
        )
        assert shuffled == canonical
        assert shuffled.step_ids == ids
        assert len(shuffled.correlation_sha256s) == 4
        assert len(set(shuffled.correlation_sha256s)) == 4
        assert shuffled.external_execution_proven is False
        assert shuffled.write_authorized is False
        assert shuffled.dispatch_authorized is False
        assert shuffled.automatic_replay_authorized is False
        assert backend.calls == 0
    finally:
        journal.close()


@pytest.mark.parametrize("order", tuple(permutations(range(3))))
def test_pending_sink_canonical_subset_is_order_independent(
    tmp_path, order,
):
    journal, ids, steps, recovered, evidence, backend = _diamond(
        tmp_path, finish_sink=False,
    )
    try:
        expected = review_synthetic_succeeded_read_bundle(
            recovered, steps, evidence[:3],
        )
        actual = review_synthetic_succeeded_read_bundle(
            recovered, steps, tuple(evidence[index] for index in order),
        )
        assert actual == expected
        assert actual.step_ids == ids[:3]
        assert actual.dispatch_authorized is False
        assert actual.automatic_replay_authorized is False
        with pytest.raises(PlannerReadSuccessBundleRejected):
            review_synthetic_succeeded_read_bundle(
                recovered, steps, evidence,
            )
        assert backend.calls == 0
    finally:
        journal.close()
