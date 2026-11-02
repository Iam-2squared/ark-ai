"""Join durable mock-only cycle hashes with registered READ receipt evidence."""

from __future__ import annotations

from dataclasses import dataclass, replace

import pytest

from ark.agency import disconnected_registered_archive_bridge as bridge
from ark.agency.contracts import CapabilityGrant, Effect, ToolCall
from ark.agency.disconnected_batch_cycle_archive import (
    archive_disconnected_batch_fixture_cycle,
)
from ark.agency.disconnected_batch_fixture_cycle import (
    simulate_disconnected_batch_fixture_cycle,
)
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
from ark.agency.disconnected_registered_batch_receipt_set import RegisteredBatchStepEvidence
from ark.agency.disconnected_registered_fixture_join import (
    review_registered_disconnected_fixture,
)
from ark.agency.disconnected_toolbox import (
    DisconnectedToolRequest,
    execute_disconnected_fixture_tool,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry

_STEP_A = "step_" + "a" * 16
_STEP_B = "step_" + "b" * 16


@dataclass
class NeverDispatch:
    calls: int = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("bridge may never dispatch ToolBackend")


def _fixture(tmp_path):
    backend = NeverDispatch()
    registry = ToolRegistry((
        ToolRegistration("math.sum", "math.sum", Effect.READ, "local:mock", backend),
    ))
    gate = PermissionGate()
    grants = (CapabilityGrant("math.sum", "sandbox:fixture", 100),)
    specs = (
        (_STEP_A, '{"values":[1,2]}', [1, 2], ()),
        (_STEP_B, '{"values":[2,3]}', [2, 3], (_STEP_A,)),
    )
    steps = tuple(
        DisconnectedBatchStep(step, "math.sum", raw, deps)
        for step, raw, _, deps in specs
    )
    plan = build_disconnected_batch_plan("req_" + "f" * 32, steps)
    schedule = build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    receipt = simulate_disconnected_batch_fixture_cycle(
        plan, schedule, retained_digest=plan.plan_digest,
    )
    archive_path = tmp_path / "cycle.json"
    saved = archive_disconnected_batch_fixture_cycle(
        receipt, plan, schedule, retained_plan_digest=plan.plan_digest,
        path=archive_path,
    )
    journal = DisconnectedReadJournal.create(tmp_path / "reads.sqlite")
    retained = genesis_witness()
    carriers = []
    for index, (step, raw, values, _) in enumerate(specs):
        call = ToolCall("math.sum", "math.sum", "sandbox:fixture", {"values": values})
        request = DisconnectedToolRequest(
            "req_" + ("a" if index == 0 else "b") * 32, "math.sum", raw,
        )
        result = execute_disconnected_fixture_tool(request)
        bound = bind_disconnected_fixture_result(request, result)
        link = review_registered_disconnected_fixture(
            registry, gate, call, grants, step, request, result, bound,
            observed_at_ms=50,
        )
        retained = journal.append(
            prepare_disconnected_read_receipt(step, request, result, bound),
            retained,
        )
        carriers.append((link, call, request, result, bound))
    evidence = tuple(
        RegisteredBatchStepEvidence(
            journal, retained, link, call, grants, request, result, binding,
        )
        for link, call, request, result, binding in carriers
    )
    return {
        "backend": backend, "registry": registry, "gate": gate,
        "plan": plan, "schedule": schedule, "evidence": evidence,
        "journal": journal, "path": archive_path, "sha": saved.file_sha256,
    }


def _review(case, **changes):
    inputs = dict(
        plan=case["plan"], schedule=case["schedule"],
        evidence=case["evidence"], registry=case["registry"], gate=case["gate"],
        retained_plan_digest=case["plan"].plan_digest,
        path=case["path"], retained_file_sha256=case["sha"],
        observed_at_ms=50,
    )
    inputs.update(changes)
    return bridge.review_registered_cycle_archive_bridge(**inputs)


def test_registered_cycle_and_archived_file_join_without_backend(tmp_path):
    case = _fixture(tmp_path)
    try:
        report = _review(case)
        assert report.step_count == 2
        assert report.cycle_file_sha256 == case["sha"]
        assert report.plan_digest == case["plan"].plan_digest
        assert len(report.join_sha256) == 64
        assert report == _review(case)
        assert report.backend_dispatched is False
        assert report.write_authorized is False
        assert report.automatic_replay_authorized is False
        assert report.consent_authenticated is False
        assert report.independent_custody_proven is False
        assert report.external_outcome_proven is False
        assert case["backend"].calls == 0
        assert not case["gate"]._consumed_tokens
    finally:
        case["journal"].close()


@pytest.mark.parametrize("mutation", (
    "wrong_file_sha", "wrong_plan_sha", "wrong_clock_type",
    "missing_read", "reversed_read",
))
def test_misaligned_inputs_do_not_join(tmp_path, mutation):
    case = _fixture(tmp_path)
    overrides = {
        "wrong_file_sha": {"retained_file_sha256": "0" * 64},
        "wrong_plan_sha": {"retained_plan_digest": "0" * 64},
        "wrong_clock_type": {"observed_at_ms": True},
        "missing_read": {"evidence": case["evidence"][:1]},
        "reversed_read": {"evidence": case["evidence"][::-1]},
    }
    try:
        with pytest.raises(bridge.RegisteredArchiveBridgeRejected):
            _review(case, **overrides[mutation])
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()


def test_late_archive_file_tamper_rejected(tmp_path):
    case = _fixture(tmp_path)
    try:
        raw = case["path"].read_bytes()
        case["path"].write_bytes(b"X" + raw[1:])
        with pytest.raises(bridge.RegisteredArchiveBridgeRejected):
            _review(case)
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()


def test_late_journal_row_tamper_rejected(tmp_path):
    case = _fixture(tmp_path)
    try:
        case["journal"]._connection.execute("UPDATE receipts SET operation='text.find'")
        with pytest.raises(bridge.RegisteredArchiveBridgeRejected):
            _review(case)
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()


def test_reflective_result_denial_cannot_forge_join_hash(tmp_path, monkeypatch):
    case = _fixture(tmp_path)

    def forged_false(self):
        object.__setattr__(self, "join_sha256", "0" * 64)
        return False

    monkeypatch.setattr(
        bridge.RegisteredArchiveBridgeReview,
        "external_outcome_proven", property(forged_false),
    )
    try:
        with pytest.raises(bridge.RegisteredArchiveBridgeRejected, match="changed"):
            _review(case)
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()


@pytest.mark.parametrize("target", (
    "step_operation", "step_arg_carrier", "request_carrier", "grants_carrier",
))
def test_second_registered_read_callback_cannot_retarget_joined_sources(
    tmp_path, monkeypatch, target,
):
    case = _fixture(tmp_path)
    native = bridge.review_registered_batch_receipt_set
    calls = [0]

    def late_mutation(*args, **kwargs):
        reviewed = native(*args, **kwargs)
        calls[0] += 1
        if calls[0] == 2:
            if target == "step_operation":
                object.__setattr__(
                    case["plan"].steps[0], "operation", "text.stats",
                )
            elif target == "step_arg_carrier":
                item = case["plan"].steps[0]
                old = item.canonical_args_json
                clone = ("!" + old)[1:]
                assert clone == old and clone is not old
                object.__setattr__(item, "canonical_args_json", clone)
            elif target == "request_carrier":
                item = case["evidence"][0]
                clone = replace(item.request)
                assert clone == item.request and clone is not item.request
                object.__setattr__(item, "request", clone)
            else:
                item = case["evidence"][0]
                clone = tuple(list(item.grants))
                assert clone == item.grants and clone is not item.grants
                object.__setattr__(item, "grants", clone)
        return reviewed

    monkeypatch.setattr(
        bridge, "review_registered_batch_receipt_set", late_mutation,
    )
    try:
        with pytest.raises(
            bridge.RegisteredArchiveBridgeRejected, match="source changed",
        ):
            _review(case)
        assert calls[0] == 2
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()
