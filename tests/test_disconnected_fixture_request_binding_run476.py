"""Opt-in request-domain evidence for disconnected in-memory READ fixtures."""

from __future__ import annotations

from dataclasses import replace

import pytest

import ark.agency.disconnected_fixture_binding as mod
from ark.agency.disconnected_toolbox import (
    DisconnectedToolRequest,
    DisconnectedToolResult,
    execute_disconnected_fixture_tool,
)


def _request(suffix="a", operation="math.sum", args='{"values":[1,2]}'):
    return DisconnectedToolRequest("req_" + suffix * 32, operation, args)


def _pair(request=None):
    request = request or _request()
    return request, execute_disconnected_fixture_tool(request)


def test_request_binding_is_deterministic_and_non_authorizing():
    request, result = _pair()
    first = mod.bind_disconnected_fixture_result(request, result)
    assert first == mod.bind_disconnected_fixture_result(request, result)
    assert len(first.request_bound_digest) == 64
    assert first.request_id == request.request_id
    assert first.result_digest == result.result_digest
    assert first.dispatch_authorized is False
    assert first.external_outcome_verified is False
    assert first.automatic_replay_authorized is False


def test_equal_fixture_outputs_do_not_share_request_binding():
    first_request, first_result = _pair(_request("a"))
    second_request, second_result = _pair(_request("b"))
    assert first_result.input_digest == second_result.input_digest
    assert first_result.result_digest == second_result.result_digest
    first = mod.bind_disconnected_fixture_result(first_request, first_result)
    second = mod.bind_disconnected_fixture_result(second_request, second_result)
    assert first.request_bound_digest != second.request_bound_digest
    with pytest.raises(mod.DisconnectedFixtureBindingRejected, match="identity"):
        mod.bind_disconnected_fixture_result(second_request, first_result)


@pytest.mark.parametrize("field,replacement", (
    ("request_id", "req_" + "b" * 32),
    ("operation", "text.find"),
    ("input_digest", "0" * 64),
    ("canonical_result_json", '{"count":2,"sum":4}'),
    ("result_digest", "f" * 64),
))
def test_rejects_tampered_fixture_result(field, replacement):
    request, result = _pair()
    with pytest.raises(mod.DisconnectedFixtureBindingRejected):
        mod.bind_disconnected_fixture_result(
            request, replace(result, **{field: replacement}),
        )


@pytest.mark.parametrize("field", (
    "dispatch_authorized",
    "automatic_replay_authorized",
    "external_outcome_known",
))
def test_result_with_forged_execution_authority_is_refused(monkeypatch, field):
    request, result = _pair()
    monkeypatch.setattr(
        DisconnectedToolResult, field, property(lambda _result: True),
    )
    with pytest.raises(mod.DisconnectedFixtureBindingRejected, match="authority"):
        mod.bind_disconnected_fixture_result(request, result)


@pytest.mark.parametrize("field", (
    "dispatch_authorized",
    "external_outcome_verified",
    "automatic_replay_authorized",
))
def test_forged_bound_receipt_authority_is_refused(monkeypatch, field):
    request, result = _pair()
    monkeypatch.setattr(
        mod.DisconnectedFixtureBinding, field, property(lambda _result: True),
    )
    with pytest.raises(mod.DisconnectedFixtureBindingRejected, match="constructed"):
        mod.bind_disconnected_fixture_result(request, result)


def test_result_carrier_mutation_during_independent_recompute_fails(monkeypatch):
    request, result = _pair()
    original = mod.execute_disconnected_fixture_tool

    def rewrite(original_request):
        same_value = bytes(result.canonical_result_json, "utf-8").decode()
        assert same_value == result.canonical_result_json
        assert same_value is not result.canonical_result_json
        object.__setattr__(result, "canonical_result_json", same_value)
        return original(original_request)

    monkeypatch.setattr(mod, "execute_disconnected_fixture_tool", rewrite)
    with pytest.raises(mod.DisconnectedFixtureBindingRejected, match="epoch"):
        mod.bind_disconnected_fixture_result(request, result)


def test_invalid_input_is_not_silently_rebound():
    request = _request(args='{"values":[1, 2]}')
    trusted = execute_disconnected_fixture_tool(_request())
    with pytest.raises(mod.DisconnectedFixtureBindingRejected):
        mod.bind_disconnected_fixture_result(request, trusted)


def test_exact_input_types_only():
    request, result = _pair()
    with pytest.raises(mod.DisconnectedFixtureBindingRejected, match="exact"):
        mod.bind_disconnected_fixture_result(request, object())
    with pytest.raises(mod.DisconnectedFixtureBindingRejected, match="exact"):
        mod.bind_disconnected_fixture_result(object(), result)
