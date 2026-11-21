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
    "__init__", "__getattribute__", "__getattr__",
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
    "result_digest", "__init__", "__getattribute__", "__getattr__",
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


def test_result_allocation_hook_poison_isolated_from_pytest_process():
    # CPython can keep the altered tp_new slot after deleting an inherited
    # __new__ attribute. This adversarial check MUST run in a child process:
    # restoring the class dict alone can corrupt unrelated subsequent tests.
    import subprocess
    import sys
    import textwrap

    script = textwrap.dedent("""
        import ark.agency.disconnected_toolbox as toolbox
        called = []

        def bad(*_args, **_kwargs):
            called.append('new')
            raise AssertionError('poisoned fixture allocation executed')

        toolbox.DisconnectedToolResult.__new__ = staticmethod(bad)
        request = toolbox.DisconnectedToolRequest(
            'req_' + 'a' * 32, 'math.sum', '{"values":[1,2]}',
        )
        try:
            toolbox.execute_disconnected_fixture_tool(request)
        except toolbox.DisconnectedToolRejected as exc:
            assert 'authority definition changed' in str(exc)
        else:
            raise AssertionError('poisoned __new__ was accepted')
        assert called == []
    """)
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True, text=True, check=False, timeout=20,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


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
        # Replaced helpers are now rejected before _run can modify __init__.
        with pytest.raises(
            toolbox.DisconnectedToolRejected,
            match="digest or JSON implementation changed",
        ):
            toolbox.execute_disconnected_fixture_tool(request)
        assert calls == []
        assert cls.__init__ is original
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
        # The preaccess helper pin stops the mutation before the request slot
        # can be replaced, rather than merely noticing after calculation.
        with pytest.raises(
            toolbox.DisconnectedToolRejected,
            match="digest or JSON implementation changed",
        ):
            toolbox.execute_disconnected_fixture_tool(request)
        assert calls == []
        assert vars(cls)["canonical_args_json"] is original
    finally:
        cls.canonical_args_json = original


def test_legitimate_disconnected_calculation_still_has_no_authority():
    result = toolbox.execute_disconnected_fixture_tool(_request())
    assert result.canonical_result_json == '{"count":2,"sum":3}'
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
