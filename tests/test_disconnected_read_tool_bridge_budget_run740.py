"""Recovered-READ mock bridge retains its original budget and deny-only helpers.

No case invokes a real ToolBackend or treats synthetic recovery as consent.
All fixtures are constructed before monkeypatching unsafe descriptors.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ark.agency import disconnected_read_tool_bridge as bridge

_REQUEST = "req_" + "a" * 32
_STEP = "step_" + "1" * 16


def _fixtures():
    step = bridge.recovery.ReadRecoveryStep(
        _STEP, "math.sum", (), "NOT_STARTED", None,
    )
    request = bridge.fixture.DisconnectedToolRequest(
        bridge.derive_disconnected_read_fixture_id(_REQUEST, _STEP),
        "math.sum", '{"values":[4,6]}',
    )
    return (step,), (bridge.DetachedReadToolBinding(_STEP, request),)


def test_original_limit_allows_readonly_fixture_and_no_authority():
    steps, bindings = _fixtures()
    outcome = bridge.preview_disconnected_read_tools(_REQUEST, steps, bindings)
    assert outcome.ready_step_ids == (_STEP,)
    assert outcome.withheld_step_ids == ()
    assert outcome.fixture_results[0].canonical_result_json == '{"count":2,"sum":10}'
    assert outcome.dispatch_authorized is False
    assert outcome.automatic_replay_authorized is False
    assert outcome.external_effect_verified is False
    assert outcome.consent_authenticated is False


@pytest.mark.parametrize("budget", (25, 10_000, True, -1))
def test_rebound_step_limit_rejected_before_any_fixture_execution(
    monkeypatch, budget,
):
    steps, bindings = _fixtures()
    monkeypatch.setattr(bridge, "_MAX_STEPS", budget)
    with pytest.raises(bridge.DisconnectedReadToolBridgeRejected, match="protocol"):
        bridge.preview_disconnected_read_tools(_REQUEST, steps, bindings)


@pytest.mark.parametrize(("field", "value"), (
    ("_DOMAIN", b"ARK-unsafe-bridge\0"),
    ("_REQUEST", object()),
    ("_STEP", object()),
))
def test_bridge_digest_domain_and_identifier_parsers_are_pinned(
    monkeypatch, field, value,
):
    steps, bindings = _fixtures()
    monkeypatch.setattr(bridge, field, value)
    with pytest.raises(bridge.DisconnectedReadToolBridgeRejected, match="protocol"):
        bridge.preview_disconnected_read_tools(_REQUEST, steps, bindings)


@pytest.mark.parametrize("codec", ("json", "hashlib"))
def test_poisoned_bridge_codec_never_receives_fixture_arguments(monkeypatch, codec):
    steps, bindings = _fixtures()
    touched = []

    def poison(*args, **kwargs):
        touched.append(codec)
        raise AssertionError("fixture arguments leaked through patched codec")

    if codec == "json":
        monkeypatch.setattr(bridge, codec, SimpleNamespace(dumps=poison))
    else:
        monkeypatch.setattr(bridge, codec, SimpleNamespace(sha256=poison))
    with pytest.raises(bridge.DisconnectedReadToolBridgeRejected, match="protocol"):
        bridge.preview_disconnected_read_tools(_REQUEST, steps, bindings)
    assert touched == []


@pytest.mark.parametrize("helper", ("recovery", "execute"))
def test_replaced_recovery_or_executor_never_runs(monkeypatch, helper):
    steps, bindings = _fixtures()
    touched = []

    def poison(*args, **kwargs):
        touched.append(helper)
        raise AssertionError("replacement callback executed")

    if helper == "recovery":
        monkeypatch.setattr(bridge.recovery, "schedule_detached_read_recovery", poison)
    else:
        monkeypatch.setattr(bridge.fixture, "execute_disconnected_fixture_tool", poison)
    with pytest.raises(bridge.DisconnectedReadToolBridgeRejected, match="protocol"):
        bridge.preview_disconnected_read_tools(_REQUEST, steps, bindings)
    assert touched == []


@pytest.mark.parametrize(("kind", "name"), (
    ("binding", "step_id"),
    ("binding", "request"),
    ("binding", "__getattribute__"),
    ("output", "fixture_results"),
    ("output", "dispatch_authorized"),
    ("output", "automatic_replay_authorized"),
    ("output", "consent_authenticated"),
))
def test_replaced_dataclass_descriptor_is_refused_before_getter(
    monkeypatch, kind, name,
):
    steps, bindings = _fixtures()
    touched = []

    def poison(_instance):
        touched.append(name)
        return False

    cls = (
        bridge.DetachedReadToolBinding
        if kind == "binding" else bridge.DetachedReadToolPreview
    )
    monkeypatch.setattr(cls, name, property(poison))
    with pytest.raises(bridge.DisconnectedReadToolBridgeRejected, match="protocol"):
        bridge.preview_disconnected_read_tools(_REQUEST, steps, bindings)
    assert touched == []


def test_derived_fixture_request_ids_are_step_specific_without_authority():
    second = "step_" + "2" * 16
    assert bridge.derive_disconnected_read_fixture_id(_REQUEST, _STEP) != (
        bridge.derive_disconnected_read_fixture_id(_REQUEST, second)
    )
    steps, bindings = _fixtures()
    mismatch = bridge.DetachedReadToolBinding(
        _STEP,
        bridge.fixture.DisconnectedToolRequest(
            bridge.derive_disconnected_read_fixture_id(_REQUEST, second),
            "math.sum", '{"values":[4,6]}',
        ),
    )
    with pytest.raises(bridge.DisconnectedReadToolBridgeRejected, match="identity"):
        bridge.preview_disconnected_read_tools(_REQUEST, steps, (mismatch,))
    assert bindings[0].request.request_id != mismatch.request.request_id
