"""Static attribute spoofing cannot make noncanonical V3 mock evidence eligible."""

import pytest

from ark.learning.gate import SimulationEvidence, simulate_gate


def _evidence(**changes: object) -> SimulationEvidence:
    values: dict[str, object] = {
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
    return SimulationEvidence(**values)  # type: ignore[arg-type]


def _rejected(report: dict[str, object]) -> None:
    assert report["simulation_decision"] == "REJECT"
    assert report["reasons"] == ["noncanonical_mock_evidence"]
    assert report["model_promotion_status"] == "NOT_EVALUATED"
    assert report["automatic_promotion"] is False
    assert report["v3_gate"] == "NOT_PASSED"


def test_stable_getter_cannot_hide_stored_regression(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    item = _evidence(
        candidate_runs=((False, False), (False, False)),
    )
    original = SimulationEvidence.__getattribute__

    def spoof_candidate_runs(self: SimulationEvidence, name: str) -> object:
        if name == "candidate_runs":
            return ((True, True), (True, True))
        return original(self, name)

    monkeypatch.setattr(
        SimulationEvidence, "__getattribute__", spoof_candidate_runs,
    )
    _rejected(simulate_gate(item))


def test_added_field_descriptor_cannot_replace_instance_storage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    item = _evidence(candidate_runs=((False, False), (False, False)))
    monkeypatch.setattr(
        SimulationEvidence,
        "candidate_runs",
        property(lambda _self: ((True, True), (True, True))),
        raising=False,
    )
    _rejected(simulate_gate(item))


def test_unexpected_instance_state_is_not_eligible() -> None:
    item = _evidence()
    item.__dict__["unexpected"] = "not part of the evidence contract"
    _rejected(simulate_gate(item))
