"""Reject noncanonical mock gate evidence; never open protected evaluation."""

from dataclasses import replace

import pytest

from ark.learning.gate import SimulationEvidence, simulate_gate
from ark.learning.training import StopRequired


def _evidence(**changes):
    fields = dict(
        baseline_runs=((True, False), (True, False)),
        candidate_runs=((True, True), (True, True)),
        controlled=True,
        provenance_reviewed=True,
        contamination_suspected=False,
        runtime_failures=0,
        memory_error=False,
    )
    fields.update(changes)
    return SimulationEvidence(**fields)


def _denied(result):
    assert result["simulation_decision"] == "REJECT"
    assert result["reasons"] == ["noncanonical_mock_evidence"]
    assert result["model_promotion_status"] == "NOT_EVALUATED"
    assert result["automatic_promotion"] is False
    assert result["v3_gate"] == "NOT_PASSED"


def test_valid_mock_policy_outcome_remains_unchanged():
    result = simulate_gate(_evidence())
    assert result["simulation_decision"] == "ELIGIBLE_IN_SIMULATION_ONLY"
    assert result["automatic_promotion"] is False
    assert result["v3_gate"] == "NOT_PASSED"


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("controlled", 1),
        ("controlled", "yes"),
        ("controlled", None),
        ("provenance_reviewed", 1),
        ("provenance_reviewed", "approved"),
        ("contamination_suspected", 0),
        ("contamination_suspected", "false"),
        ("memory_error", 0),
        ("memory_error", "false"),
        ("runtime_failures", False),
        ("runtime_failures", 0.0),
    ),
)
def test_truthy_or_equal_aliases_cannot_make_mock_eligible(field, value):
    _denied(simulate_gate(replace(_evidence(), **{field: value})))


@pytest.mark.parametrize(
    "changes",
    (
        {"baseline_runs": []},
        {"candidate_runs": [(True, True), (True, True)]},
        {"baseline_runs": ()},
        {"candidate_runs": ()},
        {"baseline_runs": ((True, False),)},
        {"candidate_runs": ((True, True),) * 3},
        {"baseline_runs": ([True, False], [True, False])},
        {"baseline_runs": ((True, 0), (True, 0))},
        {"candidate_runs": ((1, True), (1, True))},
        {"baseline_runs": ((True, False), (True, 0.0))},
        {"baseline_runs": (tuple([True] * 4097), tuple([True] * 4097))},
    ),
)
def test_inexact_or_unbounded_mock_runs_are_rejected(changes):
    _denied(simulate_gate(_evidence(**changes)))


def test_exact_false_control_still_rejects_under_existing_policy():
    result = simulate_gate(_evidence(controlled=False))
    assert result["simulation_decision"] == "REJECT"
    assert "uncontrolled" in result["reasons"]


def test_real_or_subclass_evidence_never_passes_simulation_boundary():
    with pytest.raises(StopRequired):
        simulate_gate(_evidence(measurement_kind="real"))
    with pytest.raises(StopRequired):
        simulate_gate(_evidence(measurement_kind=123))

    class DerivedEvidence(SimulationEvidence):
        pass

    with pytest.raises(StopRequired):
        simulate_gate(DerivedEvidence(**vars(_evidence())))
