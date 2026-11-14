"""Run739: disconnected mock execution refuses swapped helper graph and budgets."""

import re

import pytest

from ark.agency import disconnected_toolbox as mod


def private_request():
    return mod.DisconnectedToolRequest(
        "req_" + "a" * 32, "math.sum", '{"values":[19,23]}',
    )


@pytest.mark.parametrize("field,value", [
    ("_ID", re.compile(r".*")),
    ("_OPERATIONS", frozenset(("math.sum", "unsafe.exec"))),
    ("_DOMAIN", b"unreviewed-disconnected-tool-domain"),
    ("_MAX_INPUT", 1_000_000),
    ("_MAX_INPUT", True),
    ("_MAX_TEXT", 1_000_000),
    ("_MAX_DEPTH", 1_000),
    ("_MIN_INT", -(2**100)),
    ("_MAX_INT", 2**100),
])
def test_refuse_modified_mock_protocol_before_private_argument_read(
    monkeypatch, field, value,
):
    monkeypatch.setattr(mod, field, value)
    with pytest.raises(mod.DisconnectedToolRejected, match="changed"):
        mod.execute_disconnected_fixture_tool(private_request())


@pytest.mark.parametrize("helper", [
    "_unique_pairs", "_integer", "_reject_number", "_json",
    "_canonical", "_text", "_validate_tree", "_run",
])
def test_poisoned_mock_helper_never_receives_decoded_arguments(monkeypatch, helper):
    calls = []

    def poisoned(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("poisoned helper executed")

    monkeypatch.setattr(mod, helper, poisoned)
    with pytest.raises(mod.DisconnectedToolRejected, match="changed"):
        mod.execute_disconnected_fixture_tool(private_request())
    assert not calls


def test_genuine_mock_result_keeps_denial_contract():
    first = mod.execute_disconnected_fixture_tool(private_request())
    second = mod.execute_disconnected_fixture_tool(private_request())
    assert first == second
    assert first.canonical_result_json == '{"count":2,"sum":42}'
    assert len(first.input_digest) == len(first.result_digest) == 64
    assert first.dispatch_authorized is False
    assert first.automatic_replay_authorized is False
    assert first.external_outcome_known is False
