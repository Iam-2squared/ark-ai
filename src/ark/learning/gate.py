"""Frozen-policy simulation only; real candidate opening/decision stops for review."""

from dataclasses import dataclass

from .training import StopRequired


@dataclass(frozen=True)
class SimulationEvidence:
    baseline_runs: tuple[tuple[bool, ...], ...]
    candidate_runs: tuple[tuple[bool, ...], ...]
    controlled: bool
    provenance_reviewed: bool
    contamination_suspected: bool
    runtime_failures: int
    memory_error: bool
    measurement_kind: str = "mock"


def simulate_gate(evidence: SimulationEvidence) -> dict:
    if evidence.measurement_kind != "mock":
        raise StopRequired("STOP before real evaluation/promotion decision")
    reasons = []
    old, new = evidence.baseline_runs, evidence.candidate_runs
    if (
        len(old) != 2
        or len(new) != 2
        or not old[0]
        or len(old[0]) != len(new[0])
        or any(type(x) is not bool for run in (*old, *new) for x in run)
        or old[0] != old[1]
        or new[0] != new[1]
    ):
        reasons.append("incomplete_or_nonreproducible_evidence")
    if not evidence.controlled:
        reasons.append("uncontrolled")
    if not evidence.provenance_reviewed or evidence.contamination_suspected:
        reasons.append("provenance_or_contamination")
    if type(evidence.runtime_failures) is not int or evidence.runtime_failures != 0:
        reasons.append("runtime_failure")
    if evidence.memory_error:
        reasons.append("memory_error")
    if not reasons:
        if any(a and not b for a, b in zip(old[0], new[0], strict=True)):
            reasons.append("task_regression")
        if not any(not a and b for a, b in zip(old[0], new[0], strict=True)):
            reasons.append("no_improvement")
    return {
        "simulation_decision": "REJECT" if reasons else "ELIGIBLE_IN_SIMULATION_ONLY",
        "reasons": reasons,
        "model_promotion_status": "NOT_EVALUATED",
        "automatic_promotion": False,
        "v3_gate": "NOT_PASSED",
    }
