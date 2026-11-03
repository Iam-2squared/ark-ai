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


_EVIDENCE_FIELDS = (
    "baseline_runs", "candidate_runs", "controlled",
    "provenance_reviewed", "contamination_suspected", "runtime_failures",
    "memory_error", "measurement_kind",
)


def _reject_noncanonical_mock() -> dict:
    return {
        "simulation_decision": "REJECT",
        "reasons": ["noncanonical_mock_evidence"],
        "model_promotion_status": "NOT_EVALUATED",
        "automatic_promotion": False,
        "v3_gate": "NOT_PASSED",
    }


def simulate_gate(evidence: SimulationEvidence) -> dict:
    """Evaluate bounded exact mock evidence, never actual protected V2 runs.

    Pin the entire carrier epoch before policy evaluation and reject a
    reentrant/reflective mutation after evaluation. Only immutable tuples
    and exact primitive booleans are eligible. Neither this local simulation
    nor its output grants Candidate promotion, protected V2 opening or spend.
    """
    if type(evidence) is not SimulationEvidence:
        raise StopRequired("STOP before real evaluation/promotion decision")
    try:
        epoch = tuple(getattr(evidence, name) for name in _EVIDENCE_FIELDS)
    except (AttributeError, TypeError, ValueError) as exc:
        raise StopRequired("STOP before real evaluation/promotion decision") from exc
    (
        old, new, controlled, provenance_reviewed, contamination_suspected,
        runtime_failures, memory_error, measurement_kind,
    ) = epoch
    if type(measurement_kind) is not str or measurement_kind != "mock":
        raise StopRequired("STOP before real evaluation/promotion decision")

    def unchanged() -> bool:
        try:
            return type(evidence) is SimulationEvidence and all(
                getattr(evidence, name) is original
                for name, original in zip(_EVIDENCE_FIELDS, epoch, strict=True)
            )
        except (AttributeError, TypeError, ValueError):
            return False

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
    exact_control_flags = (
        type(controlled) is bool
        and type(provenance_reviewed) is bool
        and type(contamination_suspected) is bool
        and type(memory_error) is bool
        and type(runtime_failures) is int
    )
    if not exact_runs or not exact_control_flags or not unchanged():
        return _reject_noncanonical_mock()

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
    if not controlled:
        reasons.append("uncontrolled")
    if not provenance_reviewed or contamination_suspected:
        reasons.append("provenance_or_contamination")
    if runtime_failures != 0:
        reasons.append("runtime_failure")
    if memory_error:
        reasons.append("memory_error")
    if not reasons:
        if any(a and not b for a, b in zip(old[0], new[0], strict=True)):
            reasons.append("task_regression")
        if not any(not a and b for a, b in zip(old[0], new[0], strict=True)):
            reasons.append("no_improvement")
    # Reflective writes to a frozen dataclass, patched attribute getters or
    # callback side-effects cannot silently change the evidence underlying
    # an eligible decision. No automatic retries or grants occur here.
    if not unchanged():
        return _reject_noncanonical_mock()
    report = {
        "simulation_decision": "REJECT" if reasons else "ELIGIBLE_IN_SIMULATION_ONLY",
        "reasons": reasons,
        "model_promotion_status": "NOT_EVALUATED",
        "automatic_promotion": False,
        "v3_gate": "NOT_PASSED",
    }
    if not unchanged():
        return _reject_noncanonical_mock()
    return report
