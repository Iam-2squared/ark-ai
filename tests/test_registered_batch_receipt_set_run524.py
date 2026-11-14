"""Complete-DAG registered READ receipts: mock-only, never dispatch."""

from __future__ import annotations

from dataclasses import dataclass, replace

import pytest

import ark.agency.disconnected_registered_batch_receipt_set as batch_module
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
from ark.agency.disconnected_registered_batch_receipt_review import RegisteredBatchReceiptReview
from ark.agency.disconnected_registered_batch_receipt_set import (
    RegisteredBatchSetRejected,
    RegisteredBatchSetReview,
    RegisteredBatchStepEvidence,
    review_registered_batch_receipt_set,
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

STEP_A = "step_" + "a" * 16
STEP_B = "step_" + "b" * 16
ARGS_A = '{"values":[1,2]}'
ARGS_B = '{"values":[2,3]}'


@dataclass
class NeverDispatch:
    calls: int = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("registered batch receipt set must never dispatch")


def setup_case(tmp_path, *, count=2):
    backend = NeverDispatch()
    registry = ToolRegistry((
        ToolRegistration("math.sum", "math.sum", Effect.READ, "local:mock", backend),
    ))
    gate = PermissionGate()
    grants = (CapabilityGrant("math.sum", "sandbox:fixture", 100),)
    specs = [(STEP_A, ARGS_A, [1, 2], ())]
    if count == 2:
        specs.append((STEP_B, ARGS_B, [2, 3], (STEP_A,)))
    steps = tuple(
        DisconnectedBatchStep(step, "math.sum", raw, deps)
        for step, raw, _, deps in specs
    )
    plan = build_disconnected_batch_plan("req_" + "f" * 32, steps)
    schedule = build_disconnected_batch_schedule(
        plan, retained_digest=plan.plan_digest,
    )
    journal = DisconnectedReadJournal.create(tmp_path / "all-read.sqlite")
    retained = genesis_witness()
    carriers = []
    for index, (step, raw, values, _) in enumerate(specs):
        call = ToolCall("math.sum", "math.sum", "sandbox:fixture", {"values": values})
        request = DisconnectedToolRequest(
            "req_" + ("a" if index == 0 else "b") * 32, "math.sum", raw,
        )
        result = execute_disconnected_fixture_tool(request)
        binding = bind_disconnected_fixture_result(request, result)
        link = review_registered_disconnected_fixture(
            registry, gate, call, grants, step, request, result, binding,
            observed_at_ms=50,
        )
        retained = journal.append(
            prepare_disconnected_read_receipt(step, request, result, binding),
            retained,
        )
        carriers.append((link, call, request, result, binding))
    evidence = tuple(
        RegisteredBatchStepEvidence(
            journal, retained, link, call, grants, request, result, binding,
        )
        for link, call, request, result, binding in carriers
    )
    return {
        "backend": backend, "registry": registry, "gate": gate,
        "plan": plan, "schedule": schedule, "journal": journal, "evidence": evidence,
    }


def invoke(case, **changes):
    kwargs = {
        "plan": case["plan"], "schedule": case["schedule"],
        "retained_plan_digest": case["plan"].plan_digest,
        "evidence": case["evidence"], "registry": case["registry"],
        "gate": case["gate"], "observed_at_ms": 50,
    }
    kwargs.update(changes)
    return review_registered_batch_receipt_set(**kwargs)


@pytest.mark.parametrize("count", [1, 2])
def test_whole_dag_is_diagnostic_without_backend(tmp_path, count):
    case = setup_case(tmp_path, count=count)
    try:
        review = invoke(case)
        assert type(review) is RegisteredBatchSetReview
        assert len(review.step_receipts) == count
        assert [row[0] for row in review.step_receipts] == (
            [STEP_A] if count == 1 else [STEP_A, STEP_B]
        )
        assert [row[3] for row in review.step_receipts] == (
            [0] if count == 1 else [0, 1]
        )
        assert len(review.review_sha256) == 64
        assert review.backend_dispatched is False
        assert review.write_authorized is False
        assert review.automatic_replay_authorized is False
        assert review.dependencies_completed_proven is False
        assert review.independent_custody_proven is False
        assert case["backend"].calls == 0
        assert not case["gate"]._consumed_tokens
    finally:
        case["journal"].close()


@pytest.mark.parametrize("mutation", ["missing", "duplicate", "reverse", "extra"])
def test_incomplete_or_misordered_step_evidence_is_denied(tmp_path, mutation):
    case = setup_case(tmp_path)
    original = case["evidence"]
    choices = {
        "missing": original[:1],
        "duplicate": (original[0], original[0]),
        "reverse": original[::-1],
        "extra": original + original[:1],
    }
    try:
        with pytest.raises(RegisteredBatchSetRejected):
            invoke(case, evidence=choices[mutation])
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()


@pytest.mark.parametrize("changed", [
    {"retained_plan_digest": "f" * 64},
    {"observed_at_ms": 101},
    {"observed_at_ms": True},
])
def test_wrong_retained_digest_expiry_or_clock_type_denied(tmp_path, changed):
    case = setup_case(tmp_path)
    try:
        with pytest.raises(RegisteredBatchSetRejected):
            invoke(case, **changed)
    finally:
        case["journal"].close()


def test_tampered_sqlite_row_rejected_in_whole_batch(tmp_path):
    case = setup_case(tmp_path)
    try:
        case["journal"]._connection.execute(
            "UPDATE receipts SET operation='text.find'"
        )
        with pytest.raises(RegisteredBatchSetRejected):
            invoke(case)
    finally:
        case["journal"].close()


@pytest.mark.parametrize("field", ["review_sha256", "plan_digest"])
def test_final_false_authority_getter_must_not_rewrite_report(
    tmp_path, monkeypatch, field,
):
    case = setup_case(tmp_path)

    def forged_false(self):
        object.__setattr__(self, field, "0" * 64)
        return False

    monkeypatch.setattr(
        RegisteredBatchSetReview, "independent_custody_proven",
        property(forged_false),
    )
    try:
        with pytest.raises(RegisteredBatchSetRejected, match="result changed"):
            invoke(case)
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()


def test_final_false_denial_getter_cannot_rewrite_sqlite_history(tmp_path, monkeypatch):
    case = setup_case(tmp_path)

    def forged_false(self):
        case["journal"]._connection.execute(
            "UPDATE receipts SET operation='text.find'"
        )
        return False

    monkeypatch.setattr(
        RegisteredBatchSetReview, "independent_custody_proven",
        property(forged_false),
    )
    try:
        with pytest.raises(RegisteredBatchSetRejected):
            invoke(case)
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()


def test_true_or_integer_authority_flags_are_rejected(tmp_path, monkeypatch):
    case = setup_case(tmp_path)
    monkeypatch.setattr(
        RegisteredBatchSetReview, "backend_dispatched", property(lambda self: 1),
    )
    try:
        with pytest.raises(RegisteredBatchSetRejected, match="gained authority"):
            invoke(case)
    finally:
        case["journal"].close()


def _one_child_receipt(case):
    item = case["evidence"][0]
    return batch_module.review_registered_batch_receipt(
        case["plan"], case["schedule"], case["plan"].plan_digest,
        item.journal, item.retained_journal, item.link,
        case["registry"], case["gate"], item.call, item.grants, STEP_A,
        item.request, item.result, item.binding, observed_at_ms=50,
    )


@pytest.mark.parametrize(
    ("field", "forged_value"),
    (
        ("plan_digest", "0" * 64),
        ("schedule_digest", "0" * 64),
        ("wave_index", 1),
        ("link_sha256", "0" * 64),
        ("journal_count", 0),
        ("journal_tip_sha256", "0" * 64),
        ("review_sha256", "X" * 64),
    ),
)
def test_aggregate_independently_rejects_forged_child_fields(
    tmp_path, monkeypatch, field, forged_value,
):
    case = setup_case(tmp_path, count=1)
    try:
        valid = _one_child_receipt(case)
        forged = replace(valid, **{field: forged_value})
        monkeypatch.setattr(
            batch_module, "review_registered_batch_receipt",
            lambda *args, **kwargs: forged,
        )
        with pytest.raises(RegisteredBatchSetRejected, match="READ step receipt"):
            invoke(case)
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()


def test_aggregate_cannot_inherit_forged_child_authority(tmp_path, monkeypatch):
    case = setup_case(tmp_path, count=1)
    try:
        valid = _one_child_receipt(case)
        monkeypatch.setattr(
            batch_module, "review_registered_batch_receipt",
            lambda *args, **kwargs: valid,
        )
        monkeypatch.setattr(
            RegisteredBatchReceiptReview, "write_authorized",
            property(lambda self: 1),
        )
        with pytest.raises(RegisteredBatchSetRejected, match="gained authority"):
            invoke(case)
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()


def test_aggregate_rechecks_child_after_false_denial_getter(tmp_path, monkeypatch):
    case = setup_case(tmp_path, count=1)
    try:
        valid = _one_child_receipt(case)
        monkeypatch.setattr(
            batch_module, "review_registered_batch_receipt",
            lambda *args, **kwargs: valid,
        )

        def mutation(self):
            object.__setattr__(self, "review_sha256", "0" * 64)
            return False

        monkeypatch.setattr(
            RegisteredBatchReceiptReview, "independent_custody_proven",
            property(mutation),
        )
        with pytest.raises(RegisteredBatchSetRejected, match="changed after denial"):
            invoke(case)
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()


@pytest.mark.parametrize("forged_digest", ["0" * 64, "f" * 64])
def test_parent_recomputes_exact_child_digest_not_just_hex_shape(
    tmp_path, monkeypatch, forged_digest,
):
    case = setup_case(tmp_path, count=1)
    try:
        valid = _one_child_receipt(case)
        assert valid.review_sha256 != forged_digest
        forged = replace(valid, review_sha256=forged_digest)
        monkeypatch.setattr(
            batch_module, "review_registered_batch_receipt",
            lambda *args, **kwargs: forged,
        )
        with pytest.raises(RegisteredBatchSetRejected, match="digest disagrees"):
            invoke(case)
        assert case["backend"].calls == 0
        assert not case["gate"]._consumed_tokens
    finally:
        case["journal"].close()


class _EquivalentStrSubclass(str):
    """Equals canonical str values but is not an exact untrusted receipt type."""


@pytest.mark.parametrize("field", [
    "step_id", "plan_digest", "schedule_digest", "action_request_id",
    "fixture_request_id", "link_sha256", "journal_tip_sha256",
])
def test_parent_rejects_equivalent_child_string_subclasses(
    tmp_path, monkeypatch, field,
):
    case = setup_case(tmp_path, count=1)
    try:
        valid = _one_child_receipt(case)
        forged = replace(
            valid, **{field: _EquivalentStrSubclass(getattr(valid, field))}
        )
        assert getattr(forged, field) == getattr(valid, field)
        monkeypatch.setattr(
            batch_module, "review_registered_batch_receipt",
            lambda *args, **kwargs: forged,
        )
        with pytest.raises(
            RegisteredBatchSetRejected, match="READ step receipt disagrees",
        ):
            invoke(case)
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()


@pytest.mark.parametrize("forged_authority", [False, True])
def test_final_child_review_cannot_replace_batch_authority_descriptor(
    tmp_path, monkeypatch, forged_authority,
):
    """Even a false-valued replacement after denial is an altered result epoch."""
    case = setup_case(tmp_path, count=1)
    original_child = batch_module.review_registered_batch_receipt
    child_calls = 0

    def final_child_callback(*args, **kwargs):
        nonlocal child_calls
        result = original_child(*args, **kwargs)
        child_calls += 1
        # The parent reads a registered child three times: initial,
        # repeat, and after the first parent denial checks.
        if child_calls == 3:
            monkeypatch.setattr(
                RegisteredBatchSetReview,
                "backend_dispatched",
                property(lambda self: forged_authority),
            )
        return result

    monkeypatch.setattr(
        batch_module, "review_registered_batch_receipt", final_child_callback,
    )
    try:
        with pytest.raises(RegisteredBatchSetRejected, match="result changed"):
            invoke(case)
        assert child_calls == 3
        assert case["backend"].calls == 0
        assert not case["gate"]._consumed_tokens
    finally:
        case["journal"].close()
