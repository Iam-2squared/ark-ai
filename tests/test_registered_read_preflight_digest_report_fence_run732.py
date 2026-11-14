"""Disconnected READ plan preflight protects private grant/plan fingerprint custody.

Every backend is inert. A synthetic clock, grant, digest and resulting receipt
NEVER authorize a real READ, WRITE, paid call, or external side effect.
"""

import pytest

from ark.agency import disconnected_read_preflight as preflight
from ark.agency.contracts import CapabilityGrant, Effect, PlanStep, ToolCall
from ark.agency.planner import PlanGraph
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NoBackend:
    calls = 0

    def execute(self, call):
        self.calls += 1
        raise AssertionError("no READ preflight backend dispatch")


def _fixture():
    backend = _NoBackend()
    registry = ToolRegistry((
        ToolRegistration("fixture.read", "fixture.read", Effect.READ, "offline", backend),
    ))
    call = ToolCall("fixture.read", "fixture.read", "private", {"canary": "confidential"})
    plan = PlanGraph((PlanStep("read", call),))
    grants = (CapabilityGrant("fixture.read", "private", 1000),)
    return plan, registry, PermissionGate(), grants, backend


def _run(items):
    plan, registry, gate, grants, _backend = items
    return preflight.preview_registered_read_plan(
        plan, registry, gate, grants, observed_at_ms=100,
    )


@pytest.mark.parametrize("mutation", (
    "sha256", "json_dumps", "hashlib_module", "json_module",
    "domain", "max_steps", "max_grants", "max_ms",
))
def test_preinstalled_digest_dependencies_refuse_before_private_reads(
    monkeypatch, mutation,
):
    items = _fixture()
    hits = []

    def hostile(*args, **kwargs):
        hits.append("leaked")
        raise AssertionError("injected codec saw private input")

    if mutation == "sha256":
        monkeypatch.setattr(preflight.hashlib, "sha256", hostile)
    elif mutation == "json_dumps":
        monkeypatch.setattr(preflight.json, "dumps", hostile)
    elif mutation == "hashlib_module":
        monkeypatch.setattr(preflight, "hashlib", object())
    elif mutation == "json_module":
        monkeypatch.setattr(preflight, "json", object())
    elif mutation == "domain":
        monkeypatch.setattr(preflight, "_DOMAIN", b"forged")
    else:
        monkeypatch.setattr(preflight, "_MAX_" + mutation[4:].upper(), -1)

    with pytest.raises(
        preflight.DisconnectedReadPreflightRejected,
        match="digest dependencies changed",
    ):
        _run(items)
    assert hits == []
    assert items[-1].calls == 0
    assert items[2]._consumed_tokens == set()


@pytest.mark.parametrize("field", (
    "topology_digest", "status_digest", "registry_revision",
    "grant_fingerprint", "ready_step_ids", "ready_bound_ids",
    "fingerprint", "__getattribute__", "__new__", "__init__",
))
def test_result_descriptor_or_constructor_substitution_is_never_invoked(
    monkeypatch, field,
):
    items = _fixture()
    hits = []

    def hostile(*args, **kwargs):
        hits.append("executed")
        raise AssertionError("hostile receipt field was evaluated")

    cls = preflight.DisconnectedReadPreflight
    originally_local = field in vars(cls)
    try:
        if field == "__new__":
            # Mutating __new__ on a live CPython slotted dataclass poisons its
            # C-level tp_new slot even after monkeypatch.undo()/delattr().
            # Rebind the public class alias instead, still proving early
            # rejection before the forged constructor can run.
            forged = type("ForgedPreflight", (), {"__new__": staticmethod(hostile)})
            monkeypatch.setattr(preflight, "DisconnectedReadPreflight", forged)
        elif field.startswith("__"):
            monkeypatch.setattr(cls, field, hostile)
        else:
            monkeypatch.setattr(cls, field, property(hostile))

        with pytest.raises(
            preflight.DisconnectedReadPreflightRejected,
            match="authority descriptor changed",
        ):
            _run(items)
        assert hits == []
        assert items[-1].calls == 0
    finally:
        # Inherited object.__new__ must not be installed as an *own* class
        # attribute when a hostile __new__ fixture is undone. Doing so
        # changes dataclass construction for all later tests in this process.
        monkeypatch.undo()
        if not originally_local and field in vars(cls):
            delattr(cls, field)
    # Every hostile parametrization must leave the actual frozen dataclass
    # constructible for later tests in the same Python interpreter.
    assert type(cls("t", "s", "r", "g", (), (), "f")) is cls


@pytest.mark.parametrize("mutation", ("sha256", "json_dumps", "domain"))
def test_registry_callback_cannot_rebind_digest_before_grant_fingerprint(
    monkeypatch, mutation,
):
    items = _fixture()
    registry = items[1]
    original = registry.bind
    hits = []

    def hostile(*args, **kwargs):
        hits.append("executed")
        raise AssertionError("unexpected private digest")

    def delayed(call):
        bound = original(call)
        if mutation == "sha256":
            monkeypatch.setattr(preflight.hashlib, "sha256", hostile)
        elif mutation == "json_dumps":
            monkeypatch.setattr(preflight.json, "dumps", hostile)
        else:
            monkeypatch.setattr(preflight, "_DOMAIN", b"altered")
        return bound

    monkeypatch.setattr(registry, "bind", delayed)
    with pytest.raises(
        preflight.DisconnectedReadPreflightRejected,
        match="digest dependencies changed",
    ):
        _run(items)
    assert hits == []
    assert items[-1].calls == 0


def test_honest_read_plan_fingerprint_unchanged_and_never_grants_authority():
    items = _fixture()
    first = _run(items)
    second = _run(items)
    assert first == second
    assert len(first.fingerprint) == 64
    assert first.ready_step_ids == ("read",)
    assert first.dispatch_authorized is False
    assert first.external_result_verified is False
    assert first.authenticated_clock_or_consent is False
    assert first.automatic_replay_authorized is False
    assert "confidential" not in repr(first)
    assert items[-1].calls == 0
