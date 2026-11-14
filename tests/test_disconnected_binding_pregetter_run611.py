"""Request-bound disconnected fixture results never grant executable authority."""

import pytest

import ark.agency.disconnected_fixture_binding as binding
from ark.agency.disconnected_toolbox import (
    DisconnectedToolRequest,
    execute_disconnected_fixture_tool,
)


def _pair():
    request = DisconnectedToolRequest(
        "req_" + "a" * 32, "math.sum", '{"values":[1,2]}',
    )
    return request, execute_disconnected_fixture_tool(request)


class _FalseWithSideEffect:
    def __init__(self, calls):
        self.calls = calls

    def __get__(self, instance, owner=None):
        self.calls.append("getter")
        return False


def test_reflected_constructor_substitution_never_executes(monkeypatch):
    request, result = _pair()
    calls = []

    class Counterfeit:
        def __init__(self, *_args):
            calls.append("constructor")
            raise AssertionError("counterfeit constructed")

    monkeypatch.setattr(binding, "DisconnectedFixtureBinding", Counterfeit)
    with pytest.raises(
        binding.DisconnectedFixtureBindingRejected, match="constructed binding",
    ):
        binding.bind_disconnected_fixture_result(request, result)
    assert calls == []


@pytest.mark.parametrize("flag", binding._BINDING_DENIALS)
def test_false_property_refused_before_invocation(monkeypatch, flag):
    request, result = _pair()
    calls = []
    monkeypatch.setattr(
        binding._BINDING_TYPE, flag, _FalseWithSideEffect(calls),
    )
    with pytest.raises(
        binding.DisconnectedFixtureBindingRejected, match="constructed binding",
    ):
        binding.bind_disconnected_fixture_result(request, result)
    assert calls == []


@pytest.mark.parametrize("flag", binding._BINDING_DENIALS)
def test_reentrant_result_field_cannot_arm_denial(monkeypatch, flag):
    request, result = _pair()
    cls = binding._BINDING_TYPE
    original = cls.__getattribute__
    calls = []
    injected = [False]

    def on_result_field(self, name):
        value = original(self, name)
        if name == "request_bound_digest" and not injected[0]:
            injected[0] = True
            monkeypatch.setattr(cls, flag, _FalseWithSideEffect(calls))
        return value

    monkeypatch.setattr(cls, "__getattribute__", on_result_field)
    with pytest.raises(
        binding.DisconnectedFixtureBindingRejected, match="constructed binding",
    ):
        binding.bind_disconnected_fixture_result(request, result)
    assert injected == [True]
    assert calls == []


def test_hash_callback_cannot_replace_result_constructor(monkeypatch):
    request, result = _pair()
    calls = []
    original_sha256 = binding.hashlib.sha256

    class Counterfeit:
        def __init__(self, *_args):
            calls.append("constructor")
            raise AssertionError("counterfeit constructed")

    def inject(payload=b""):
        if payload.startswith(binding._DOMAIN):
            monkeypatch.setattr(binding, "DisconnectedFixtureBinding", Counterfeit)
        return original_sha256(payload)

    monkeypatch.setattr(binding.hashlib, "sha256", inject)
    with pytest.raises(
        binding.DisconnectedFixtureBindingRejected, match="fixture recomputation rejected",
    ):
        binding.bind_disconnected_fixture_result(request, result)
    assert calls == []


def test_ordinary_request_bound_fixture_stays_non_authorizing():
    request, result = _pair()
    bound = binding.bind_disconnected_fixture_result(request, result)
    assert bound.request_id == request.request_id
    assert bound.dispatch_authorized is False
    assert bound.external_outcome_verified is False
    assert bound.automatic_replay_authorized is False
