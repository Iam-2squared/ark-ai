"""Restart-safe local act_/req_/journal reconciliation, never a real READ grant."""

from dataclasses import replace

import pytest

import ark.agency.disconnected_registered_receipt_review as review
from ark.agency.contracts import CapabilityGrant, Effect, ToolCall
from ark.agency.disconnected_fixture_binding import bind_disconnected_fixture_result
from ark.agency.disconnected_read_journal import (
    DisconnectedReadJournal,
    ReadReceipt,
    genesis_witness,
)
from ark.agency.disconnected_read_receipt_bridge import prepare_disconnected_read_receipt
from ark.agency.disconnected_registered_fixture_join import (
    review_registered_disconnected_fixture,
)
from ark.agency.disconnected_toolbox import (
    DisconnectedToolRequest,
    execute_disconnected_fixture_tool,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry

STEP = "step_" + "a" * 16


class ForbiddenBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("real backend must not run")


def make_case(tmp_path, *, effect=Effect.READ):
    backend = ForbiddenBackend()
    registry = ToolRegistry((
        ToolRegistration("math.sum", "math.sum", effect, "local:mock", backend),
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
    ) if effect is Effect.READ else None
    path = tmp_path / "read-restart.sqlite"
    journal = DisconnectedReadJournal.create(path)
    retained = journal.append(
        prepare_disconnected_read_receipt(STEP, request, result, binding),
        genesis_witness(),
    )
    return (
        journal, retained, link, registry, gate, call, grants, STEP,
        request, result, binding, backend, path,
    )


def invoke(case, *, observed_at_ms=50):
    return review.review_retained_registered_receipt(
        *case[:11], observed_at_ms=observed_at_ms,
    )


def test_reopen_uses_one_snapshot_without_dispatch(tmp_path):
    case = make_case(tmp_path)
    case[0].close()
    with DisconnectedReadJournal.open(case[-1]) as reopened:
        restored = (reopened, *case[1:])
        output = invoke(restored)
        assert type(output) is review.RegisteredReceiptReview
        assert output.action_request_id == case[5].request_id
        assert output.fixture_request_id == case[8].request_id
        assert output.link_sha256 == case[2].link_sha256
        assert output.journal_count == 1
        assert output.journal_tip_sha256 == case[1].tip_sha256
        assert not any((
            output.backend_dispatched, output.external_effect_proven,
            output.replay_authorized, output.independent_custody_proven,
        ))
        assert case[-2].calls == 0
        assert case[4]._consumed_tokens == set()


def test_diagnostic_review_is_repeatable_and_does_not_append(tmp_path):
    case = make_case(tmp_path)
    try:
        first = invoke(case)
        second = invoke(case)
        assert first == second
        assert case[0].verify(case[1]) == case[1]
        assert case[-2].calls == 0
    finally:
        case[0].close()


@pytest.mark.parametrize(
    "field,value",
    (
        ("fixture_request_id", "req_" + "f" * 32),
        ("action_request_id", "act_" + "f" * 64),
        ("registry_revision", "f" * 64),
        ("result_digest", "f" * 64),
        ("link_sha256", "f" * 64),
    ),
)
def test_unretained_link_substitution_rejected(tmp_path, field, value):
    case = list(make_case(tmp_path))
    try:
        case[2] = replace(case[2], **{field: value})
        with pytest.raises(review.RegisteredReceiptReviewRejected, match="differs"):
            invoke(case)
    finally:
        case[0].close()


def test_stale_witness_cannot_hide_later_sqlite_append(tmp_path):
    case = make_case(tmp_path)
    try:
        newer = ReadReceipt(
            "req_" + "b" * 32, "step_" + "b" * 16,
            "math.sum", "a" * 64, "b" * 64,
        )
        case[0].append(newer, case[1])
        with pytest.raises(review.RegisteredReceiptReviewRejected, match="snapshot"):
            invoke(case)
        assert case[-2].calls == 0
    finally:
        case[0].close()


def test_tampered_sqlite_row_cannot_pass_a_retained_chain(tmp_path):
    case = make_case(tmp_path)
    try:
        case[0]._connection.execute(
            "UPDATE receipts SET result_digest=? WHERE seq=1",
            ("f" * 64,),
        )
        with pytest.raises(review.RegisteredReceiptReviewRejected):
            invoke(case)
    finally:
        case[0].close()


def test_deleted_sqlite_receipt_is_not_an_approved_effect(tmp_path):
    case = make_case(tmp_path)
    try:
        case[0]._connection.execute("DELETE FROM receipts WHERE seq=1")
        with pytest.raises(review.RegisteredReceiptReviewRejected):
            invoke(case)
    finally:
        case[0].close()


def test_unexpected_clock_changes_original_link(tmp_path):
    case = make_case(tmp_path)
    try:
        with pytest.raises(review.RegisteredReceiptReviewRejected, match="differs"):
            invoke(case, observed_at_ms=51)
    finally:
        case[0].close()


@pytest.mark.parametrize(
    "grants",
    (
        (),
        (CapabilityGrant("math.sum", "sandbox:fixture", 49),),
        (CapabilityGrant("math.sum", "sandbox:wrong", 100),),
    ),
)
def test_revoked_expired_or_wrong_scope_grant_denied(tmp_path, grants):
    case = list(make_case(tmp_path))
    try:
        case[6] = grants
        with pytest.raises(review.RegisteredReceiptReviewRejected):
            invoke(case)
    finally:
        case[0].close()


def test_no_write_registration_can_be_rebound(tmp_path):
    case = list(make_case(tmp_path))
    try:
        backend = case[-2]
        case[3] = ToolRegistry((
            ToolRegistration("math.sum", "math.sum", Effect.WRITE, "local:mock", backend),
        ))
        with pytest.raises(review.RegisteredReceiptReviewRejected):
            invoke(case)
        assert not case[4]._consumed_tokens
    finally:
        case[0].close()


def test_mutated_original_call_is_not_explained_by_old_link(tmp_path):
    case = make_case(tmp_path)
    try:
        object.__setattr__(case[5], "arguments", {"values": [3, 4]})
        with pytest.raises(review.RegisteredReceiptReviewRejected):
            invoke(case)
    finally:
        case[0].close()


def test_injected_scan_mutation_of_link_rejected(tmp_path, monkeypatch):
    case = make_case(tmp_path)
    original = review.DisconnectedReadJournal._scan
    link = case[2]

    def changed(self):
        witness = original(self)
        object.__setattr__(link, "result_digest", "f" * 64)
        return witness

    monkeypatch.setattr(review.DisconnectedReadJournal, "_scan", changed)
    try:
        with pytest.raises(review.RegisteredReceiptReviewRejected, match="changed"):
            invoke(case)
        assert case[-2].calls == 0
    finally:
        case[0].close()


def test_injected_authority_on_review_output_is_rejected(tmp_path, monkeypatch):
    case = make_case(tmp_path)
    monkeypatch.setattr(
        review.RegisteredReceiptReview,
        "replay_authorized", property(lambda _: True),
    )
    try:
        with pytest.raises(review.RegisteredReceiptReviewRejected, match="authority"):
            invoke(case)
    finally:
        case[0].close()
