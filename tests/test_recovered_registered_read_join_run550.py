"""Recovered mock READ -> SQLite -> ToolRegistry join regression tests."""

from __future__ import annotations

from dataclasses import dataclass, replace

import pytest

import ark.agency.disconnected_recovered_registered_read_join as joined
from ark.agency.contracts import CapabilityGrant, Effect, ToolCall
from ark.agency.disconnected_batch_plan import (
    DisconnectedBatchStep,
    build_disconnected_batch_plan,
)
from ark.agency.disconnected_batch_schedule import build_disconnected_batch_schedule
from ark.agency.disconnected_fixture_binding import bind_disconnected_fixture_result
from ark.agency.disconnected_read_journal import (
    DisconnectedReadJournal,
    genesis_witness,
)
from ark.agency.disconnected_read_receipt_bridge import prepare_disconnected_read_receipt
from ark.agency.disconnected_read_recovery_schedule import ReadRecoveryStep
from ark.agency.disconnected_registered_batch_receipt_set import (
    RegisteredBatchStepEvidence,
)
from ark.agency.disconnected_registered_fixture_join import (
    review_registered_disconnected_fixture,
)
from ark.agency.disconnected_toolbox import (
    DisconnectedToolRequest,
    execute_disconnected_fixture_tool,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry

REQUEST = "req_" + "f" * 32
A = "step_" + "a" * 16
B = "step_" + "b" * 16
ARGS_A = '{"values":[1,2]}'
ARGS_B = '{"values":[2,3]}'


@dataclass
class ForbiddenBackend:
    calls: int = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("a recovery join cannot invoke ToolBackend")


def make_case(tmp_path, states=("SUCCEEDED", "SUCCEEDED")):
    backend = ForbiddenBackend()
    registry = ToolRegistry((
        ToolRegistration("math.sum", "math.sum", Effect.READ, "mock:1", backend),
    ))
    gate = PermissionGate()
    grants = (CapabilityGrant("math.sum", "sandbox:fixture", 100),)
    specs = ((A, ARGS_A, [1, 2], ()), (B, ARGS_B, [2, 3], (A,)))
    plan = build_disconnected_batch_plan(
        REQUEST,
        tuple(
            DisconnectedBatchStep(step, "math.sum", raw, deps)
            for step, raw, _, deps in specs
        ),
    )
    schedule = build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    journal = DisconnectedReadJournal.create(tmp_path / "recover-register.sqlite")
    retained = genesis_witness()
    steps = []
    evidence_rows = []
    for (step_id, raw, values, deps), state in zip(specs, states, strict=True):
        if state == "SUCCEEDED":
            call = ToolCall(
                "math.sum", "math.sum", "sandbox:fixture", {"values": values},
            )
            request = DisconnectedToolRequest(REQUEST, "math.sum", raw)
            result = execute_disconnected_fixture_tool(request)
            binding = bind_disconnected_fixture_result(request, result)
            link = review_registered_disconnected_fixture(
                registry, gate, call, grants, step_id, request,
                result, binding, observed_at_ms=50,
            )
            retained = journal.append(
                prepare_disconnected_read_receipt(step_id, request, result, binding),
                retained,
            )
            evidence_rows.append(
                (link, call, request, result, binding),
            )
            steps.append(
                ReadRecoveryStep(
                    step_id, "math.sum", deps, state, result.result_digest,
                ),
            )
        else:
            steps.append(ReadRecoveryStep(step_id, "math.sum", deps, state))
    evidence = tuple(
        RegisteredBatchStepEvidence(
            journal, retained, link, call, grants, request, result, binding,
        )
        for link, call, request, result, binding in evidence_rows
    )
    snapshot = journal.recover_receipts(retained)
    return {
        "backend": backend, "registry": registry, "gate": gate,
        "plan": plan, "schedule": schedule, "steps": tuple(steps),
        "journal": journal, "snapshot": snapshot, "retained": retained,
        "evidence": evidence,
    }


def invoke(case, **changes):
    kwargs = {
        "plan": case["plan"], "schedule": case["schedule"],
        "steps": case["steps"], "snapshot": case["snapshot"],
        "retained_journal": case["retained"], "evidence": case["evidence"],
        "registry": case["registry"], "gate": case["gate"],
        "retained_plan_digest": case["plan"].plan_digest,
        "observed_at_ms": 50,
    }
    kwargs.update(changes)
    return joined.review_recovered_registered_reads(**kwargs)


@pytest.mark.parametrize(
    "states,successful",
    (
        (("SUCCEEDED", "SUCCEEDED"), (A, B)),
        (("SUCCEEDED", "FAILED"), (A,)),
        (("SUCCEEDED", "NOT_STARTED"), (A,)),
        (("SUCCEEDED", "UNKNOWN"), (A,)),
        (("NOT_STARTED", "NOT_STARTED"), ()),
    ),
)
def test_join_is_inert_and_accepts_only_evidenced_success(
    tmp_path, states, successful,
):
    case = make_case(tmp_path, states)
    try:
        report = invoke(case)
        assert type(report) is joined.RecoveredRegisteredReadReview
        assert tuple(x[0] for x in report.registered_steps) == successful
        assert len(report.join_sha256) == 64
        assert report.journal_tip_sha256 == case["retained"].tip_sha256
        assert report.backend_dispatched is False
        assert report.write_authorized is False
        assert report.automatic_replay_authorized is False
        assert report.external_outcome_proven is False
        assert report.independent_custody_proven is False
        assert case["backend"].calls == 0
        assert not case["gate"]._consumed_tokens
    finally:
        case["journal"].close()


@pytest.mark.parametrize("variant", ("missing", "duplicate", "reverse", "extra"))
def test_complete_and_ordered_registered_subset_required(tmp_path, variant):
    case = make_case(tmp_path)
    original = case["evidence"]
    bad = {
        "missing": original[:1],
        "duplicate": (original[0], original[0]),
        "reverse": original[::-1],
        "extra": original + original[:1],
    }[variant]
    try:
        with pytest.raises(joined.RecoveredRegisteredReadRejected):
            invoke(case, evidence=bad)
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()


def test_wrong_result_or_operation_in_recovery_is_denied(tmp_path):
    case = make_case(tmp_path)
    try:
        wrong_result = (
            replace(case["steps"][0], result_sha256="0" * 64), case["steps"][1],
        )
        wrong_operation = (
            replace(case["steps"][0], operation="text.find"), case["steps"][1],
        )
        for wrong in (wrong_result, wrong_operation):
            with pytest.raises(joined.RecoveredRegisteredReadRejected):
                invoke(case, steps=wrong)
    finally:
        case["journal"].close()


@pytest.mark.parametrize("bad_clock", (True, 100, -1, 2**63, "50"))
def test_exact_and_unexpired_observed_clock_required(tmp_path, bad_clock):
    case = make_case(tmp_path)
    try:
        with pytest.raises(joined.RecoveredRegisteredReadRejected):
            invoke(case, observed_at_ms=bad_clock)
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()


def test_old_or_foreign_journal_tip_is_denied(tmp_path):
    case = make_case(tmp_path)
    try:
        with pytest.raises(joined.RecoveredRegisteredReadRejected):
            invoke(case, retained_journal=genesis_witness())
        with pytest.raises(joined.RecoveredRegisteredReadRejected):
            invoke(case, retained_plan_digest="0" * 64)
    finally:
        case["journal"].close()


def test_sqlite_row_mutation_after_snapshot_is_denied(tmp_path):
    case = make_case(tmp_path)
    try:
        case["journal"]._connection.execute(
            "UPDATE receipts SET operation='text.find' WHERE step_id=?", (B,),
        )
        with pytest.raises(joined.RecoveredRegisteredReadRejected):
            invoke(case)
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()


def test_registered_fixture_identity_must_match_shared_request(tmp_path):
    case = make_case(tmp_path)
    try:
        second = case["evidence"][1]
        foreign = replace(
            second, request=replace(second.request, request_id="req_" + "1" * 32),
        )
        with pytest.raises(joined.RecoveredRegisteredReadRejected):
            invoke(case, evidence=(case["evidence"][0], foreign))
    finally:
        case["journal"].close()


def test_forged_child_review_digest_cannot_pass_parent(
    tmp_path, monkeypatch,
):
    case = make_case(tmp_path)
    original = joined.review_registered_batch_receipt

    def forge(*args, **kwargs):
        child = original(*args, **kwargs)
        return replace(child, review_sha256="0" * 64)

    monkeypatch.setattr(joined, "review_registered_batch_receipt", forge)
    try:
        with pytest.raises(joined.RecoveredRegisteredReadRejected):
            invoke(case)
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()


def test_registered_recheck_cannot_mutate_recovery_step(
    tmp_path, monkeypatch,
):
    case = make_case(tmp_path)
    original = joined.review_registered_batch_receipt

    def mutate(*args, **kwargs):
        child = original(*args, **kwargs)
        object.__setattr__(case["steps"][0], "state", "UNKNOWN")
        return child

    monkeypatch.setattr(joined, "review_registered_batch_receipt", mutate)
    try:
        with pytest.raises(joined.RecoveredRegisteredReadRejected):
            invoke(case)
    finally:
        case["journal"].close()


def test_recovered_join_never_returns_authority_from_forged_getter(
    tmp_path, monkeypatch,
):
    case = make_case(tmp_path)
    monkeypatch.setattr(
        joined.RecoveredRegisteredReadReview, "write_authorized",
        property(lambda self: True),
    )
    try:
        with pytest.raises(joined.RecoveredRegisteredReadRejected):
            invoke(case)
        assert case["backend"].calls == 0
        assert not case["gate"]._consumed_tokens
    finally:
        case["journal"].close()


@pytest.mark.parametrize(
    "states",
    (("SUCCEEDED", "SUCCEEDED"), ("SUCCEEDED", "FAILED")),
)
def test_recovered_sqlite_request_cannot_be_replayed_under_another_plan(
    tmp_path, states,
):
    """A valid registry/journal read is not evidence for another DAG request."""
    case = make_case(tmp_path, states)
    foreign = build_disconnected_batch_plan(
        "req_" + "e" * 32, case["plan"].steps,
    )
    foreign_schedule = build_disconnected_batch_schedule(
        foreign, retained_digest=foreign.plan_digest,
    )
    try:
        with pytest.raises(
            joined.RecoveredRegisteredReadRejected,
            match="recovery report or digest disagrees",
        ):
            invoke(
                case, plan=foreign, schedule=foreign_schedule,
                retained_plan_digest=foreign.plan_digest,
            )
        assert case["backend"].calls == 0
        assert not case["gate"]._consumed_tokens
    finally:
        case["journal"].close()
