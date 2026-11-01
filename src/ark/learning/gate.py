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
    """Evaluate bounded, exact-typed *mock* evidence, never actual V2 runs.

    Malformed synthetic inputs cannot become simulation-eligible through
    Python truthiness (1 == True) or sequence equality aliases. This is
    input hardening only; valid frozen policy outcomes are unchanged.
    """
    if (
        type(evidence) is not SimulationEvidence
        or type(evidence.measurement_kind) is not str
        or evidence.measurement_kind != "mock"
    ):
        raise StopRequired("STOP before real evaluation/promotion decision")
    old, new = evidence.baseline_runs, evidence.candidate_runs
    exact_runs = (
        type(old) is tuple
        and type(new) is tuple
        and len(old) == len(new) == 2
        and all(
            type(run) is tuple
            and 1 <= len(run) <= 4096
            and all(type(answer) is bool for answer in run)
            for run in (*old, *new)
        )
    )
    exact_control_flags = all(
        type(getattr(evidence, field)) is bool
        for field in (
            "controlled", "provenance_reviewed",
            "contamination_suspected", "memory_error",
        )
    ) and type(evidence.runtime_failures) is int
    if not exact_runs or not exact_control_flags:
        return {
            "simulation_decision": "REJECT",
            "reasons": ["noncanonical_mock_evidence"],
            "model_promotion_status": "NOT_EVALUATED",
            "automatic_promotion": False,
            "v3_gate": "NOT_PASSED",
        }
    reasons = []
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
