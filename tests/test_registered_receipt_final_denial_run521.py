"""Final denial-boundary custody for retained registered READ receipts.

All fixtures are disconnected. These tests must never invoke the backend,
grant real READ/WRITE, or authorize replay after a SQLite COMMIT.
"""

from __future__ import annotations

from dataclasses import dataclass

import pytest

from ark.agency.contracts import CapabilityGrant, Effect, ToolCall
from ark.agency.disconnected_fixture_binding import bind_disconnected_fixture_result
from ark.agency.disconnected_read_journal import (
    DisconnectedReadJournal,
    genesis_witness,
)
from ark.agency.disconnected_read_receipt_bridge import prepare_disconnected_read_receipt
from ark.agency.disconnected_registered_fixture_join import (
    review_registered_disconnected_fixture,
)
from ark.agency.disconnected_registered_receipt_review import (
    RegisteredReceiptReview,
    RegisteredReceiptReviewRejected,
    review_retained_registered_receipt,
)
from ark.agency.disconnected_toolbox import (
    DisconnectedToolRequest,
    execute_disconnected_fixture_tool,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry

STEP = "step_" + "a" * 16


@dataclass
class ForbiddenBackend:
    calls: int = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("registered READ review must never dispatch")


def build(tmp_path):
    backend = ForbiddenBackend()
    registry = ToolRegistry((
        ToolRegistration("math.sum", "math.sum", Effect.READ, "local:mock", backend),
    ))
    gate = PermissionGate()
    call = ToolCall(
        "math.sum", "math.sum", "sandbox:fixture", {"values": [1, 2]},
    )
    grants = (CapabilityGrant("math.sum", "sandbox:fixture", 100),)
    request = DisconnectedToolRequest(
        "req_" + "a" * 32, "math.sum", '{"values":[1,2]}',
    )
    result = execute_disconnected_fixture_tool(request)
    binding = bind_disconnected_fixture_result(request, result)
    link = review_registered_disconnected_fixture(
        registry, gate, call, grants, STEP, request, result, binding,
        observed_at_ms=50,
    )
    journal = DisconnectedReadJournal.create(tmp_path / "read-final-denial.sqlite")
    retained = journal.append(
        prepare_disconnected_read_receipt(STEP, request, result, binding),
        genesis_witness(),
    )
    return {
        "backend": backend,
        "registry": registry,
        "gate": gate,
        "call": call,
        "grants": grants,
        "request": request,
        "result": result,
        "binding": binding,
        "link": link,
        "journal": journal,
        "retained": retained,
    }


def invoke(case):
    return review_retained_registered_receipt(
        case["journal"], case["retained"], case["link"], case["registry"],
        case["gate"], case["call"], case["grants"], STEP, case["request"],
        case["result"], case["binding"], observed_at_ms=50,
    )


def test_untampered_reconciliation_remains_diagnostic(tmp_path):
    case = build(tmp_path)
    try:
        output = invoke(case)
        assert type(output) is RegisteredReceiptReview
        assert output.fixture_request_id == case["request"].request_id
        assert output.link_sha256 == case["link"].link_sha256
        assert output.journal_tip_sha256 == case["retained"].tip_sha256
        assert case["backend"].calls == 0
        assert case["gate"]._consumed_tokens == set()
    finally:
        case["journal"].close()


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("step_id", "step_" + "f" * 16),
        ("action_request_id", "act_" + "f" * 64),
        ("fixture_request_id", "req_" + "f" * 32),
        ("link_sha256", "f" * 64),
        ("journal_count", 999),
        ("journal_tip_sha256", "f" * 64),
    ),
)
def test_false_last_denial_getter_cannot_mutate_output(
    tmp_path, monkeypatch, field, replacement,
):
    case = build(tmp_path)

    def late_mutation(self):
        object.__setattr__(self, field, replacement)
        return False

    monkeypatch.setattr(
        RegisteredReceiptReview,
        "independent_custody_proven",
        property(late_mutation),
    )
    try:
        with pytest.raises(RegisteredReceiptReviewRejected, match="authority"):
            invoke(case)
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()


@pytest.mark.parametrize(
    "target,field,replacement",
    (
        ("link", "result_digest", "f" * 64),
        ("retained", "tip_sha256", "f" * 64),
        ("call", "arguments", {"values": [5, 6]}),
        ("grants", "expires_at_ms", 0),
        ("result", "result_digest", "f" * 64),
    ),
)
def test_false_last_denial_getter_cannot_mutate_retained_sources(
    tmp_path, monkeypatch, target, field, replacement,
):
    case = build(tmp_path)

    def late_mutation(self):
        original = case[target][0] if target == "grants" else case[target]
        object.__setattr__(original, field, replacement)
        return False

    monkeypatch.setattr(
        RegisteredReceiptReview,
        "independent_custody_proven",
        property(late_mutation),
    )
    try:
        with pytest.raises(RegisteredReceiptReviewRejected):
            invoke(case)
        assert case["backend"].calls == 0
    finally:
        case["journal"].close()
