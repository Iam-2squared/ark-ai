"""Recovered RUNNING/terminal sink never borrows detached READ evidence.

All local fixture receipts were constructed, but only actually SUCCEEDED
Planner steps may be correlated. Reopening the Planner cannot treat a
RUNNING crash as a completed READ. No backend, consent or WRITE authority.
"""

from __future__ import annotations

import pytest
from test_planner_diamond_independent_read_receipts_run690 import _diamond

from ark.agency.contracts import StepState
from ark.agency.disconnected_planner_success_bundle_review import (
    PlannerReadSuccessBundleRejected,
    review_synthetic_succeeded_read_bundle,
)
from ark.agency.planner_journal_review import SyntheticPlanJournal


@pytest.mark.parametrize(
    ("terminal", "expected"),
    (
        (None, "running"),
        (StepState.FAILED, "failed"),
        (StepState.CANCELLED, "cancelled"),
    ),
)
def test_only_three_succeeded_reads_can_bind_during_unknown_or_terminal_sink(
    tmp_path, terminal, expected,
):
    reads, ids, steps, partial, evidence, backend = _diamond(
        tmp_path, finish_sink=False,
    )
    try:
        path = tmp_path / "planner.sqlite"
        writer = SyntheticPlanJournal(path, steps)
        writer.append(
            ids[3], StepState.RUNNING, expected_revision=0, at_ms=70,
            retained=writer.recover().tail,
        )
        if terminal is not None:
            writer.append(
                ids[3], terminal, expected_revision=1, at_ms=71,
                retained=writer.recover().tail,
            )

        cold = SyntheticPlanJournal(path, steps).recover()
        assert cold.step_statuses[-1] != ()  # retained order is canonical by ID
        states = {name: state for name, state, _ in cold.step_statuses}
        assert states[ids[3]] == expected
        assert cold.ambiguous_running_steps == ((ids[3],) if terminal is None else ())
        assert cold.dispatch_authorized is False
        assert cold.automatic_replay_authorized is False

        three = review_synthetic_succeeded_read_bundle(
            cold, steps, evidence[:3][::-1],
        )
        assert three.step_ids == ids[:3]
        assert three.external_execution_proven is False
        assert three.write_authorized is False
        assert three.dispatch_authorized is False
        assert three.automatic_replay_authorized is False
        with pytest.raises(PlannerReadSuccessBundleRejected):
            review_synthetic_succeeded_read_bundle(cold, steps, evidence)
        assert backend.calls == 0
    finally:
        reads.close()


def test_sink_success_requires_its_own_registered_read_after_restart(tmp_path):
    reads, ids, steps, _partial, evidence, backend = _diamond(
        tmp_path, finish_sink=False,
    )
    try:
        path = tmp_path / "planner.sqlite"
        writer = SyntheticPlanJournal(path, steps)
        writer.append(
            ids[3], StepState.RUNNING, expected_revision=0, at_ms=70,
            retained=writer.recover().tail,
        )
        writer.append(
            ids[3], StepState.SUCCEEDED, expected_revision=1, at_ms=71,
            retained=writer.recover().tail,
        )
        cold = SyntheticPlanJournal(path, steps).recover()
        assert cold.ambiguous_running_steps == ()
        with pytest.raises(PlannerReadSuccessBundleRejected):
            review_synthetic_succeeded_read_bundle(cold, steps, evidence[:3])
        final = review_synthetic_succeeded_read_bundle(
            cold, steps, evidence[::-1],
        )
        assert final.step_ids == ids
        assert len(set(final.correlation_sha256s)) == 4
        assert final.external_execution_proven is False
        assert final.write_authorized is False
        assert final.dispatch_authorized is False
        assert backend.calls == 0
    finally:
        reads.close()
