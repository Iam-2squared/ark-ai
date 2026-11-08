"""Detached tool fixtures must not send private JSON to swapped primitives.

Local deterministic in-memory calculations only. No ToolBackend, external
dispatch, authenticated consent, or automatic replay is involved.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

import ark.agency.disconnected_toolbox as toolbox


def _request():
    return toolbox.DisconnectedToolRequest(
        "req_" + "a" * 32, "math.sum", '{"values":[1,2]}',
    )


@pytest.mark.parametrize(
    "mutation",
    ("hash_module", "sha256", "json_module", "loads", "dumps", "domain"),
)
def test_preinstalled_digest_or_json_hook_denied_before_fixture_data(
    monkeypatch, mutation,
):
    called = []

    def hostile(*_args, **_kwargs):
        called.append(True)
        raise AssertionError("untrusted fixture JSON or digest hook invoked")

    request = _request()
    with monkeypatch.context() as patch:
        if mutation == "hash_module":
            patch.setattr(toolbox, "hashlib", SimpleNamespace(sha256=hostile))
        elif mutation == "sha256":
            patch.setattr(toolbox.hashlib, "sha256", hostile)
        elif mutation == "json_module":
            patch.setattr(
                toolbox, "json", SimpleNamespace(loads=hostile, dumps=hostile),
            )
        elif mutation in ("loads", "dumps"):
            patch.setattr(toolbox.json, mutation, hostile)
        else:
            patch.setattr(toolbox, "_DOMAIN", bytes(toolbox._DOMAIN) + b"bad")
        with pytest.raises(
            toolbox.DisconnectedToolRejected,
            match="digest or JSON implementation changed",
        ):
            toolbox.execute_disconnected_fixture_tool(request)
    assert called == []


def test_reentrant_calculation_cannot_replace_digest_before_hash(monkeypatch):
    request = _request()
    original_run = toolbox._run
    called = []

    def hostile(*_args, **_kwargs):
        called.append(True)
        raise AssertionError("untrusted digest hook invoked")

    with monkeypatch.context() as patch:
        def mutated(operation, args):
            value = original_run(operation, args)
            patch.setattr(toolbox, "hashlib", SimpleNamespace(sha256=hostile))
            return value

        patch.setattr(toolbox, "_run", mutated)
        with pytest.raises(
            toolbox.DisconnectedToolRejected,
            match="digest or JSON implementation changed",
        ):
            toolbox.execute_disconnected_fixture_tool(request)
    assert called == []


def test_unmodified_fixture_still_does_not_grant_action_authority():
    result = toolbox.execute_disconnected_fixture_tool(_request())
    assert result.canonical_result_json == '{"count":2,"sum":3}'
    assert result.dispatch_authorized is False
    assert result.automatic_replay_authorized is False
    assert result.external_outcome_known is False
