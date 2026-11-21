"""Regression: a module-shadowed builtin must never consume fixture values."""

import pytest

import ark.agency.disconnected_toolbox as toolbox


def _synthetic_sum():
    return toolbox.DisconnectedToolRequest(
        "req_" + "a" * 32, "math.sum", '{"values":[2,3]}'
    )


def test_disconnected_math_uses_unshadowed_builtin() -> None:
    outcome = toolbox.execute_disconnected_fixture_tool(_synthetic_sum())
    assert outcome.canonical_result_json == '{"count":2,"sum":5}'
    assert outcome.dispatch_authorized is False
    assert outcome.external_outcome_known is False


def test_disconnected_math_denies_shadowed_module_sum_before_callback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoked: list[object] = []

    def hostile_sum(values: object) -> int:
        invoked.append(values)
        return 5

    monkeypatch.setattr(toolbox, "sum", hostile_sum, raising=False)
    with pytest.raises(toolbox.DisconnectedToolRejected, match="implementation changed"):
        toolbox.execute_disconnected_fixture_tool(_synthetic_sum())
    assert invoked == []


def test_shadowed_sum_also_refuses_unrelated_tool_before_private_json(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoked: list[object] = []
    monkeypatch.setattr(toolbox, "sum", lambda x: invoked.append(x), raising=False)
    candidate = toolbox.DisconnectedToolRequest(
        "req_" + "b" * 32, "text.stats", '{"text":"private sample"}'
    )
    with pytest.raises(toolbox.DisconnectedToolRejected, match="implementation changed"):
        toolbox.execute_disconnected_fixture_tool(candidate)
    assert not invoked
