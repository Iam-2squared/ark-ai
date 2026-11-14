"""Mock fixture results remain deny-only under reflected Python callbacks."""

from __future__ import annotations

import pytest

import ark.agency.disconnected_toolbox as toolbox


def _request():
    return toolbox.DisconnectedToolRequest(
        "req_" + "a" * 32, "math.sum", '{"values":[1,2,3]}',
    )


def test_unmodified_fixture_is_deterministic_and_deny_only():
    one = toolbox.execute_disconnected_fixture_tool(_request())
    two = toolbox.execute_disconnected_fixture_tool(_request())
    assert one == two
    assert one.canonical_result_json == '{"count":3,"sum":6}'
    assert one.dispatch_authorized is False
    assert one.automatic_replay_authorized is False
    assert one.external_outcome_known is False


@pytest.mark.parametrize("name", toolbox._DENIAL_NAMES)
def test_false_looking_descriptor_replacement_is_rejected_before_processing(
    monkeypatch, name,
):
    monkeypatch.setattr(
        toolbox.DisconnectedToolResult, name, property(lambda _: False),
    )

    def no_parse(_raw):
        pytest.fail("private fixture JSON reached after authority was replaced")

    monkeypatch.setattr(toolbox, "_json", no_parse)
    # Helper substitution now fails even before the original denial descriptor
    # check; the private parser still must not be called.
    with pytest.raises(
        toolbox.DisconnectedToolRejected, match="digest or JSON implementation changed",
    ):
        toolbox.execute_disconnected_fixture_tool(_request())


@pytest.mark.parametrize("name", toolbox._DENIAL_NAMES)
def test_true_descriptor_replacement_is_rejected_before_processing(
    monkeypatch, name,
):
    monkeypatch.setattr(
        toolbox.DisconnectedToolResult, name, property(lambda _: True),
    )
    with pytest.raises(
        toolbox.DisconnectedToolRejected, match="authority definition changed",
    ):
        toolbox.execute_disconnected_fixture_tool(_request())


def test_false_denial_getter_cannot_retarget_result_digest(monkeypatch):
    original = toolbox.DisconnectedToolResult.__getattribute__
    calls = []

    def retarget(self, name):
        calls.append(name)
        if name == "dispatch_authorized":
            object.__setattr__(self, "result_digest", "f" * 64)
            return False
        return original(self, name)

    monkeypatch.setattr(
        toolbox.DisconnectedToolResult, "__getattribute__", retarget,
    )
    with pytest.raises(
        toolbox.DisconnectedToolRejected,
        match="authority definition changed",
    ):
        toolbox.execute_disconnected_fixture_tool(_request())
    assert calls == []


def test_first_denial_getter_cannot_replace_next_authority_property(monkeypatch):
    original = toolbox.DisconnectedToolResult.__getattribute__

    def retarget(self, name):
        if name == "dispatch_authorized":
            monkeypatch.setattr(
                toolbox.DisconnectedToolResult,
                "automatic_replay_authorized",
                property(lambda _: False),
            )
            return False
        return original(self, name)

    monkeypatch.setattr(
        toolbox.DisconnectedToolResult, "__getattribute__", retarget,
    )
    with pytest.raises(
        toolbox.DisconnectedToolRejected, match="authority definition changed",
    ):
        toolbox.execute_disconnected_fixture_tool(_request())
