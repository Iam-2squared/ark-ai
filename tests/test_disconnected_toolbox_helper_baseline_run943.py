"""Run943: disconnected mock helper baseline cannot be broadened or deleted.

All inputs are synthetic. No ToolBackend, clock, permission, or external
executor can be invoked by these tests.
"""

import pytest

from ark.agency import disconnected_toolbox as toolbox


def _request():
    return toolbox.DisconnectedToolRequest(
        "req_" + "a" * 32, "math.sum", '{"values":[19,23]}',
    )


@pytest.mark.parametrize("helper", (
    "_unique_pairs", "_integer", "_reject_number", "_json",
    "_canonical", "_text", "_validate_tree", "_run",
))
def test_missing_original_helper_fails_closed_with_typed_denial(monkeypatch, helper):
    # Removing a helper from module globals must fail before _json can
    # consume synthetic private arguments, rather than leaking KeyError.
    monkeypatch.delattr(toolbox, helper)
    with pytest.raises(toolbox.DisconnectedToolRejected, match="changed"):
        toolbox.execute_disconnected_fixture_tool(_request())


def test_reference_helper_map_cannot_be_mutated_after_import():
    with pytest.raises(TypeError):
        toolbox._ORIGINAL_HELPERS["_run"] = lambda *_a: {"unsafe": True}


def test_rebound_helper_baseline_does_not_authorize_original_request(monkeypatch):
    replacement = dict(toolbox._ORIGINAL_HELPERS)
    monkeypatch.setattr(toolbox, "_ORIGINAL_HELPERS", replacement)
    with pytest.raises(toolbox.DisconnectedToolRejected, match="changed"):
        toolbox.execute_disconnected_fixture_tool(_request())


def test_original_helper_baseline_preserves_offline_math_only():
    result = toolbox.execute_disconnected_fixture_tool(_request())
    assert result.canonical_result_json == '{"count":2,"sum":42}'
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
