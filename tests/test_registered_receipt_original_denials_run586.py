"""Retained registered READ review refuses substituted deny-only properties."""

from __future__ import annotations

import pytest

import ark.agency.disconnected_registered_receipt_review as review
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
from ark.agency.disconnected_toolbox import (
    DisconnectedToolRequest,
    execute_disconnected_fixture_tool,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NoBackend:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("registered receipt review must never dispatch")


def _case(tmp_path):
    backend = _NoBackend()
    registry = ToolRegistry((
        ToolRegistration("math.sum", "math.sum", Effect.READ, "mock:1", backend),
    ))
    gate = PermissionGate()
    call = ToolCall("math.sum", "math.sum", "scope:private", {"values": [1, 2]})
    grants = (CapabilityGrant("math.sum", "scope:private", 100),)
    step = "step_" + "a" * 16
    request = DisconnectedToolRequest(
        "req_" + "a" * 32, "math.sum", '{"values":[1,2]}',
    )
    result = execute_disconnected_fixture_tool(request)
    binding = bind_disconnected_fixture_result(request, result)
    link = review_registered_disconnected_fixture(
        registry, gate, call, grants, step, request, result, binding,
        observed_at_ms=50,
    )
    journal = DisconnectedReadJournal.create(tmp_path / "registered-guards.sqlite")
    retained = journal.append(
        prepare_disconnected_read_receipt(step, request, result, binding),
        genesis_witness(),
    )
    return (
        journal, retained, link, registry, gate, call, grants,
        step, request, result, binding, backend,
    )


def _review(case):
    return review.review_retained_registered_receipt(
        *case[:11], observed_at_ms=50,
    )


@pytest.mark.parametrize("name", review._REVIEW_DENIALS)
def test_false_looking_result_getter_substitution_rejected(tmp_path, monkeypatch, name):
    case = _case(tmp_path)
    monkeypatch.setattr(review.RegisteredReceiptReview, name, property(lambda _: False))
    try:
        with pytest.raises(
            review.RegisteredReceiptReviewRejected, match="authority definition changed",
        ):
            _review(case)
        assert case[-1].calls == 0
    finally:
        case[0].close()


@pytest.mark.parametrize("name", review._LINK_DENIALS)
def test_false_looking_retained_link_getter_substitution_rejected(
    tmp_path, monkeypatch, name,
):
    case = _case(tmp_path)
    monkeypatch.setattr(review.RegisteredFixtureLink, name, property(lambda _: False))
    try:
        with pytest.raises(
            review.RegisteredReceiptReviewRejected, match="authority definition changed",
        ):
            _review(case)
        assert case[-1].calls == 0
    finally:
        case[0].close()


def test_result_getter_cannot_replace_another_denial_after_sqlite_commit(
    tmp_path, monkeypatch,
):
    case = _case(tmp_path)
    original = review.RegisteredReceiptReview.__getattribute__

    def mutate(self, name):
        if name == "backend_dispatched":
            monkeypatch.setattr(
                review.RegisteredReceiptReview,
                "replay_authorized", property(lambda _: False),
            )
            return False
        return original(self, name)

    monkeypatch.setattr(review.RegisteredReceiptReview, "__getattribute__", mutate)
    try:
        with pytest.raises(
            review.RegisteredReceiptReviewRejected, match="authority definition changed",
        ):
            _review(case)
        assert case[-1].calls == 0
    finally:
        case[0].close()


def test_original_link_and_review_are_digest_only_and_inert(tmp_path):
    case = _case(tmp_path)
    try:
        outcome = _review(case)
        assert outcome.backend_dispatched is False
        assert outcome.external_effect_proven is False
        assert outcome.replay_authorized is False
        assert outcome.independent_custody_proven is False
        assert case[-1].calls == 0
        assert case[4]._consumed_tokens == set()
    finally:
        case[0].close()


@pytest.mark.parametrize(
    ("carrier", "name"),
    (
        # Isolate __new__ mutations in a child process if subsequently tested:
        # restoring inherited object.__new__ through monkeypatch can poison
        # subsequent dataclass constructors in this pytest interpreter.
        tuple(("review", name) for name in (
            *review._REVIEW_FIELDS, "__init__", "__getattribute__", "__getattr__",
        ))
        + tuple(("link", name) for name in (
            *review._LINK_FIELDS, "__init__", "__getattribute__", "__getattr__",
        ))
    ),
)
def test_original_fields_and_hooks_are_checked_before_journal_access(
    tmp_path, monkeypatch, carrier, name,
):
    """A False-looking replacement must not even enter retained SQLite."""
    case = _case(tmp_path)
    cls = (
        review.RegisteredReceiptReview if carrier == "review"
        else review.RegisteredFixtureLink
    )

    def forbidden(*_args, **_kwargs):
        pytest.fail("substituted carrier entered the retained READ journal")

    def substituted(*_args, **_kwargs):
        pytest.fail("substituted constructor, field or lookup hook ran")

    try:
        with monkeypatch.context() as isolated:
            isolated.setattr(case[0], "_scan", forbidden)
            if name in ("__init__", "__new__", "__getattribute__", "__getattr__"):
                isolated.setattr(cls, name, substituted, raising=False)
            else:
                isolated.setattr(cls, name, property(substituted))
            with pytest.raises(
                review.RegisteredReceiptReviewRejected,
                match="authority definition changed",
            ):
                _review(case)
        assert case[-1].calls == 0
        assert case[4]._consumed_tokens == set()
    finally:
        case[0].close()


@pytest.mark.parametrize("carrier", ("review", "link"))
def test_replaced_carrier_symbol_is_rejected_before_reading_journal(
    tmp_path, monkeypatch, carrier,
):
    case = _case(tmp_path)

    def forbidden(*_args, **_kwargs):
        pytest.fail("substituted class entered retained READ journal")

    try:
        with monkeypatch.context() as isolated:
            isolated.setattr(case[0], "_scan", forbidden)
            isolated.setattr(
                review,
                "RegisteredReceiptReview" if carrier == "review"
                else "RegisteredFixtureLink",
                object,
            )
            with pytest.raises(
                review.RegisteredReceiptReviewRejected,
                match="authority definition changed",
            ):
                _review(case)
        assert case[-1].calls == 0
    finally:
        case[0].close()
