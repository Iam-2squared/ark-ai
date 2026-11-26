"""Cross-check independent act_/req_ identities without backend execution."""

from dataclasses import replace

import pytest

import ark.agency.disconnected_registered_fixture_join as join
from ark.agency.contracts import CapabilityGrant, Effect, ToolCall
from ark.agency.disconnected_fixture_binding import bind_disconnected_fixture_result
from ark.agency.disconnected_read_journal import ReadReceipt
from ark.agency.disconnected_toolbox import (
    DisconnectedToolRequest,
    execute_disconnected_fixture_tool,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry

STEP = "step_" + "a" * 16


class NoDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("real backend execution forbidden")


def fixture(*, effect=Effect.READ, args=None, name="math.sum", identifier="a"):
    backend = NoDispatch()
    reg = ToolRegistry((
        ToolRegistration("math.sum", "math.sum", effect, "local:mock", backend),
    ))
    call = ToolCall(
        name, "math.sum", "sandbox:fixture",
        {"values": [1, 2]} if args is None else args,
    )
    gate = PermissionGate()
    grants = (CapabilityGrant("math.sum", "sandbox:fixture", 100),)
    request = DisconnectedToolRequest(
        "req_" + identifier * 32, "math.sum", '{"values":[1,2]}',
    )
    result = execute_disconnected_fixture_tool(request)
    binding = bind_disconnected_fixture_result(request, result)
    return reg, gate, call, grants, request, result, binding, backend


def invoke(items, *, step_id=STEP, observed_at_ms=50):
    reg, gate, call, grants, req, result, binding, _ = items
    return join.review_registered_disconnected_fixture(
        reg, gate, call, grants, step_id, req, result, binding,
        observed_at_ms=observed_at_ms,
    )


def test_exact_local_join_is_inert_and_has_separate_request_namespaces():
    items = fixture()
    r = invoke(items)
    reg, gate, call, _, req, result, binding, backend = items
    assert type(r) is join.RegisteredFixtureLink
    assert r.step_id == STEP
    assert r.action_request_id == call.request_id
    assert r.action_request_id.startswith("act_")
    assert r.fixture_request_id == req.request_id
    assert r.fixture_request_id.startswith("req_")
    assert r.action_request_id != r.fixture_request_id
    assert r.registry_revision == reg.revision
    assert r.bound_action_id == reg.bind(call).bound_action_id
    assert r.request_bound_digest == binding.request_bound_digest
    assert r.result_digest == result.result_digest
    assert len(r.link_sha256) == 64
    assert not any((
        r.backend_dispatched, r.external_result_proven,
        r.write_authorized, r.replay_authorized,
        r.trusted_clock_or_consent_proven,
    ))
    assert backend.calls == 0 and not gate._consumed_tokens
    assert '{"values"' not in repr(r)


def test_repeatable_link_never_claims_external_effect():
    case = fixture()
    assert invoke(case) == invoke(case)
    assert case[-1].calls == 0


def test_distinct_local_fixture_identifiers_create_distinct_links():
    one = invoke(fixture(identifier="a"))
    other = invoke(fixture(identifier="b"))
    assert one.action_request_id == other.action_request_id
    assert one.fixture_request_id != other.fixture_request_id
    assert one.link_sha256 != other.link_sha256


def test_clock_is_inert_part_of_fingerprint_not_proof():
    case = fixture()
    first = invoke(case, observed_at_ms=25)
    second = invoke(case, observed_at_ms=26)
    assert first.link_sha256 != second.link_sha256
    assert not second.trusted_clock_or_consent_proven


def test_prepare_only_does_not_construct_sqlite_or_call_backend(monkeypatch):
    case = fixture()
    def blocked(*_args, **_kwargs):
        raise AssertionError("join must not persist a journal")
    monkeypatch.setattr(join, "ReadReceipt", blocked, raising=False)
    assert invoke(case).backend_dispatched is False
    assert case[-1].calls == 0


@pytest.mark.parametrize("step", ("other", "step_" + "A" * 16, True, None))
def test_invalid_step_is_denied(step):
    case = fixture()
    with pytest.raises(join.RegisteredFixtureLinkRejected, match="exact bounded"):
        invoke(case, step_id=step)
    assert case[-1].calls == 0


@pytest.mark.parametrize("clock", (True, -1, 2**63, "50", 50.0))
def test_untrusted_clock_requires_exact_bounded_integer(clock):
    case = fixture()
    with pytest.raises(join.RegisteredFixtureLinkRejected, match="exact bounded"):
        invoke(case, observed_at_ms=clock)
    assert case[-1].calls == 0


@pytest.mark.parametrize("mode", ("missing", "scope", "capability", "expired"))
def test_missing_or_stale_exact_permission_does_not_link(mode):
    case = list(fixture())
    claims = {
        "missing": (),
        "scope": (CapabilityGrant("math.sum", "sandbox:other"),),
        "capability": (CapabilityGrant("other", "sandbox:fixture"),),
        "expired": (CapabilityGrant("math.sum", "sandbox:fixture", 49),),
    }
    case[3] = claims[mode]
    with pytest.raises(join.RegisteredFixtureLinkRejected, match="grant denied"):
        invoke(tuple(case))
    assert case[-1].calls == 0


def test_write_registration_cannot_be_disguised_as_read():
    case = fixture(effect=Effect.WRITE)
    with pytest.raises(join.RegisteredFixtureLinkRejected, match="grant denied"):
        invoke(case)
    assert case[-1].calls == 0
    assert not case[1]._consumed_tokens


@pytest.mark.parametrize(
    "changes",
    (
        {"args": {"values": [1, 3]}},
        {"args": {"values": [1, 2], "unused": True}},
        {"name": "text.stats"},
    ),
)
def test_wrong_action_to_fixture_correlation_denied(changes):
    case = fixture(**changes)
    with pytest.raises(
        join.RegisteredFixtureLinkRejected,
        match="registered arguments|operation differ",
    ):
        invoke(case)
    assert case[-1].calls == 0


def test_different_result_or_request_bound_witness_denied():
    case = list(fixture())
    case[5] = replace(case[5], result_digest="f" * 64)
    with pytest.raises(join.RegisteredFixtureLinkRejected, match="fixture"):
        invoke(tuple(case))
    second = list(fixture())
    second[6] = replace(second[6], request_bound_digest="f" * 64)
    with pytest.raises(join.RegisteredFixtureLinkRejected, match="fixture"):
        invoke(tuple(second))


def test_substituted_canonical_fixture_input_denied():
    case = list(fixture())
    case[4] = replace(case[4], canonical_args_json='{"values":[1, 2]}')
    with pytest.raises(join.RegisteredFixtureLinkRejected, match="canonical fixture input"):
        invoke(tuple(case))


def test_late_mutation_during_grant_review_cannot_make_a_valid_link(monkeypatch):
    case = fixture()
    req = case[4]
    old = join.review_disconnected_registered_read

    def mutated(*args, **kwargs):
        report = old(*args, **kwargs)
        object.__setattr__(req, "operation", "text.stats")
        return report

    monkeypatch.setattr(join, "review_disconnected_registered_read", mutated)
    with pytest.raises(join.RegisteredFixtureLinkRejected, match="changed"):
        invoke(case)
    assert case[-1].calls == 0


def test_forged_receipt_from_reentrant_callback_does_not_link(monkeypatch):
    case = fixture()
    original = join.prepare_disconnected_read_receipt

    def altered(*args, **kwargs):
        receipt = original(*args, **kwargs)
        return ReadReceipt(
            receipt.request_id, receipt.step_id, receipt.operation,
            receipt.input_digest, "f" * 64,
        )

    monkeypatch.setattr(join, "prepare_disconnected_read_receipt", altered)
    with pytest.raises(join.RegisteredFixtureLinkRejected, match="receipt"):
        invoke(case)


def test_denial_flag_injected_into_return_value_is_not_authority(monkeypatch):
    case = fixture()
    monkeypatch.setattr(
        join.RegisteredFixtureLink, "write_authorized", property(lambda _: True),
    )
    with pytest.raises(join.RegisteredFixtureLinkRejected, match="authority"):
        invoke(case)
    assert case[-1].calls == 0


def test_mutable_frozen_result_replaced_at_constructor_is_rejected(monkeypatch):
    case = fixture()
    original = join._RESULT

    def altered(*args):
        report = original(*args)
        object.__setattr__(report, "bound_action_id", "bound_" + "f" * 64)
        return report

    monkeypatch.setattr(join, "_RESULT", altered)
    with pytest.raises(join.RegisteredFixtureLinkRejected, match="authority"):
        invoke(case)
