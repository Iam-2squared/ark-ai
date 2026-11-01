"""Mock-only gate evidence must remain stable throughout policy calculation."""

from dataclasses import replace

import pytest

from ark.learning.gate import SimulationEvidence, simulate_gate
from ark.learning.training import StopRequired


def evidence(**changes):
    values = {
        "baseline_runs": ((True, False), (True, False)),
        "candidate_runs": ((True, True), (True, True)),
        "controlled": True,
        "provenance_reviewed": True,
        "contamination_suspected": False,
        "runtime_failures": 0,
        "memory_error": False,
        "measurement_kind": "mock",
    }
    values.update(changes)
    return SimulationEvidence(**values)


def rejected(value):
    assert value["simulation_decision"] == "REJECT"
    assert value["reasons"] == ["noncanonical_mock_evidence"]
    assert value["model_promotion_status"] == "NOT_EVALUATED"
    assert value["automatic_promotion"] is False
    assert value["v3_gate"] == "NOT_PASSED"


def test_unchanged_mock_still_only_eligible_in_simulation():
    r = simulate_gate(evidence())
    assert r["simulation_decision"] == "ELIGIBLE_IN_SIMULATION_ONLY"
    assert r["automatic_promotion"] is False
    assert r["v3_gate"] == "NOT_PASSED"


@pytest.mark.parametrize(
    "changes,reason",
    (
        ({"controlled": False}, "uncontrolled"),
        ({"provenance_reviewed": False}, "provenance_or_contamination"),
        ({"contamination_suspected": True}, "provenance_or_contamination"),
        ({"runtime_failures": 1}, "runtime_failure"),
        ({"memory_error": True}, "memory_error"),
        ({"candidate_runs": ((True, False), (True, False))}, "no_improvement"),
        ({"candidate_runs": ((False, True), (False, True))}, "task_regression"),
    ),
)
def test_existing_mock_rejection_policy_unchanged(changes, reason):
    report = simulate_gate(evidence(**changes))
    assert report["simulation_decision"] == "REJECT"
    assert reason in report["reasons"]
    assert report["automatic_promotion"] is False


@pytest.mark.parametrize(
    "modified",
    (
        {"controlled": False},
        {"provenance_reviewed": False},
        {"contamination_suspected": True},
        {"memory_error": True},
        {"measurement_kind": "real"},
        {"baseline_runs": ((False, False), (False, False))},
    ),
)
def test_reentrant_late_evidence_change_cannot_make_mock_eligible(
    monkeypatch, modified,
):
    item = evidence()
    original = SimulationEvidence.__getattribute__
    calls = 0

    def late_change(self, field):
        nonlocal calls
        value = original(self, field)
        if field == "runtime_failures":
            calls += 1
            if calls == 2:
                for name, updated in modified.items():
                    object.__setattr__(self, name, updated)
        return value

    monkeypatch.setattr(SimulationEvidence, "__getattribute__", late_change)
    rejected(simulate_gate(item))


def test_last_measurement_kind_getter_cannot_mutate_evidence_silently(monkeypatch):
    item = evidence()
    original = SimulationEvidence.__getattribute__
    reads = 0

    def late_change(self, field):
        nonlocal reads
        value = original(self, field)
        if field == "measurement_kind":
            reads += 1
            if reads == 2:
                object.__setattr__(self, "memory_error", True)
        return value

    monkeypatch.setattr(SimulationEvidence, "__getattribute__", late_change)
    rejected(simulate_gate(item))


def test_original_tuple_reference_replacement_is_rejected(monkeypatch):
    item = evidence()
    original = SimulationEvidence.__getattribute__
    reads = 0

    def swap_same_values(self, field):
        nonlocal reads
        value = original(self, field)
        if field == "runtime_failures":
            reads += 1
            if reads == 2:
                object.__setattr__(
                    self, "candidate_runs",
                    tuple(tuple(value for value in run) for run in self.candidate_runs),
                )
        return value

    monkeypatch.setattr(SimulationEvidence, "__getattribute__", swap_same_values)
    rejected(simulate_gate(item))


def test_real_evidence_is_never_simulated():
    with pytest.raises(StopRequired):
        simulate_gate(replace(evidence(), measurement_kind="real"))
