"""Run749: disconnected arithmetic cannot execute replaced builtins on private JSON.

This is a memory-only mock, not a real ToolBackend or authorization grant.
"""

import builtins
from types import SimpleNamespace

import pytest

from ark.agency import disconnected_toolbox as toolbox


def _request(operation="math.sum", raw='{"values":[19,23]}'):
    return toolbox.DisconnectedToolRequest("req_" + "a" * 32, operation, raw)


@pytest.mark.parametrize("operation,raw", [
    ("math.sum", '{"values":[19,23]}'),
    ("text.stats", '{"text":"private fixture text"}'),
    ("json.inspect", '{"json":"[1,2,3]"}'),
])
def test_replaced_builtin_sum_is_refused_without_execution(
    monkeypatch, operation, raw,
):
    called = []

    def poisoned(*args, **kwargs):
        called.append((args, kwargs))
        raise AssertionError("substituted builtin executed")

    # Use a restricted context: a patched process-wide builtin must not leak
    # into pytest or the next independent test.
    with monkeypatch.context() as patch:
        patch.setattr(builtins, "sum", poisoned)
        try:
            toolbox.execute_disconnected_fixture_tool(_request(operation, raw))
        except toolbox.DisconnectedToolRejected as exc:
            assert "implementation changed" in str(exc)
        else:
            raise AssertionError("replaced builtin admitted")
    assert called == []


@pytest.mark.parametrize("operation,raw", [
    ("math.sum", '{"values":[19,23]}'),
    ("text.find", '{"needle":"a","text":"private"}'),
])
def test_replaced_builtins_module_is_refused_before_private_fixture_read(
    monkeypatch, operation, raw,
):
    called = []

    def poisoned(*args, **kwargs):
        called.append((args, kwargs))
        raise AssertionError("forged builtin executed")

    with monkeypatch.context() as patch:
        patch.setattr(toolbox, "builtins", SimpleNamespace(sum=poisoned))
        with pytest.raises(
            toolbox.DisconnectedToolRejected,
            match="implementation changed",
        ):
            toolbox.execute_disconnected_fixture_tool(_request(operation, raw))
    assert called == []


def test_unmodified_builtin_sum_keeps_deterministic_result_and_denials():
    result = toolbox.execute_disconnected_fixture_tool(_request())
    assert result.canonical_result_json == '{"count":2,"sum":42}'
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
