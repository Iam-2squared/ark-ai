"""Disconnected calculations must reject poisoned carrier descriptors before access.

All cases are local, in-memory and synthetic; no backend or action is invoked.
"""

from __future__ import annotations

from contextlib import contextmanager

import pytest

import ark.agency.disconnected_toolbox as toolbox

_MISSING = object()


def _request():
    return toolbox.DisconnectedToolRequest(
        "req_" + "a" * 32, "math.sum", '{"values":[1,2]}',
    )


@contextmanager
def _poison(cls, name, calls):
    original = vars(cls).get(name, _MISSING)

    def bad(*_args, **_kwargs):
        calls.append(name)
        raise AssertionError("poisoned fixture descriptor executed")

    replacement = property(bad) if name in (
        "request_id", "operation", "canonical_args_json",
        "input_digest", "canonical_result_json", "result_digest",
    ) else staticmethod(bad) if name == "__new__" else bad
    setattr(cls, name, replacement)
    try:
        yield
    finally:
        # Never leave inherited hooks as new own attributes after teardown.
        if original is _MISSING:
            delattr(cls, name)
        else:
            setattr(cls, name, original)


@pytest.mark.parametrize("name", (
    "request_id", "operation", "canonical_args_json",
    "__init__", "__new__", "__getattribute__", "__getattr__",
))
def test_poisoned_request_carrier_rejected_before_private_json_access(name):
    request = _request()
    calls = []
    with _poison(toolbox.DisconnectedToolRequest, name, calls):
        with pytest.raises(
            toolbox.DisconnectedToolRejected,
            match="request descriptor changed",
        ):
            toolbox.execute_disconnected_fixture_tool(request)
        assert calls == []


@pytest.mark.parametrize("name", (
    "request_id", "operation", "input_digest", "canonical_result_json",
    "result_digest", "__init__", "__new__", "__getattribute__", "__getattr__",
))
def test_poisoned_result_carrier_rejected_before_fixture_execution(name):
    request = _request()
    calls = []
    with _poison(toolbox.DisconnectedToolResult, name, calls):
        with pytest.raises(
            toolbox.DisconnectedToolRejected,
            match="authority definition changed",
        ):
            toolbox.execute_disconnected_fixture_tool(request)
        assert calls == []


def test_constructor_hook_changed_during_calculation_is_rejected(monkeypatch):
    request = _request()
    execute = toolbox._run
    cls = toolbox.DisconnectedToolResult
    original = vars(cls)["__init__"]
    calls = []

    def bad(*_args, **_kwargs):
        calls.append("constructor")
        raise AssertionError("poisoned result constructor executed")

    def changed(operation, args):
        result = execute(operation, args)
        cls.__init__ = bad
        return result

    monkeypatch.setattr(toolbox, "_run", changed)
    try:
        with pytest.raises(
            toolbox.DisconnectedToolRejected,
            match="authority definition changed",
        ):
            toolbox.execute_disconnected_fixture_tool(request)
        assert calls == []
    finally:
        cls.__init__ = original


def test_request_field_hook_changed_during_calculation_is_rejected(monkeypatch):
    request = _request()
    execute = toolbox._run
    cls = toolbox.DisconnectedToolRequest
    original = vars(cls)["canonical_args_json"]
    calls = []

    def bad(_self):
        calls.append("json")
        raise AssertionError("poisoned request field executed")

    def changed(operation, args):
        result = execute(operation, args)
        cls.canonical_args_json = property(bad)
        return result

    monkeypatch.setattr(toolbox, "_run", changed)
    try:
        with pytest.raises(
            toolbox.DisconnectedToolRejected,
            match="request descriptor changed",
        ):
            toolbox.execute_disconnected_fixture_tool(request)
        assert calls == []
    finally:
        cls.canonical_args_json = original


def test_legitimate_disconnected_calculation_still_has_no_authority():
    result = toolbox.execute_disconnected_fixture_tool(_request())
    assert result.canonical_result_json == '{"count":2,"sum":3}'
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
