"""Registry must not rebind a reflectively swapped, equal-text ToolCall.

Disconnected registration identity only; no authenticated issuer, durable
authorization, external backend execution or automatic WRITE dispatch.
"""

import pytest

import ark.agency.registry as registry_module
from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class RefuseDispatch:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("registry review must never execute a backend")


def _fixture():
    backend = RefuseDispatch()
    entry = ToolRegistration(
        "fixture-reader", "offline.read", Effect.READ, "local-only", backend,
    )
    registry = ToolRegistry((entry,))
    call = ToolCall("fixture-reader", "offline.read", "fixture-scope", {"n": 1})
    return registry, call, entry, backend


def _equal_new_string(value: str) -> str:
    copied = ("!" + value)[1:]
    assert copied == value and copied is not value
    return copied


@pytest.mark.parametrize("field", ("tool", "capability", "scope"))
@pytest.mark.parametrize("operation", ("resolve", "bind"))
def test_lookup_callback_cannot_replace_equal_original_call_carrier(
    monkeypatch, field, operation,
):
    registry, call, entry, backend = _fixture()
    original = getattr(call, field)
    real_get = registry.get
    reached = []

    def get_with_swap(name):
        found = real_get(name)
        assert found is entry
        object.__setattr__(call, field, _equal_new_string(original))
        reached.append("swapped")
        return found

    monkeypatch.setattr(registry, "get", get_with_swap)
    with pytest.raises(ValueError, match="ToolCall identity changed"):
        getattr(registry, operation)(call)
    assert reached == ["swapped"]
    assert backend.calls == 0


@pytest.mark.parametrize("field", ("tool", "capability", "scope"))
def test_binding_rejects_resolve_callback_equal_carrier_replacement(
    monkeypatch, field,
):
    registry, call, entry, backend = _fixture()
    original = getattr(call, field)
    real_resolve = registry.resolve

    def resolve_with_swap(request):
        resolved = real_resolve(request)
        assert resolved is entry
        object.__setattr__(call, field, _equal_new_string(original))
        return resolved

    monkeypatch.setattr(registry, "resolve", resolve_with_swap)
    with pytest.raises(ValueError, match="registry binding"):
        registry.bind(call)
    assert backend.calls == 0


@pytest.mark.parametrize("field", ("tool", "capability", "scope"))
def test_bound_identity_hash_cannot_hide_equal_text_swap(
    monkeypatch, field,
):
    registry, call, _entry, backend = _fixture()
    original = getattr(call, field)
    real_json = registry_module._canonical_json
    reached = []

    def hash_with_swap(value):
        encoded = real_json(value)
        # This call's final binding payload is distinct from the registry
        # revision payload; mutate only after the original binding hash.
        if isinstance(value, dict) and "request_id" in value:
            object.__setattr__(call, field, _equal_new_string(original))
            reached.append("bound-hash")
        return encoded

    monkeypatch.setattr(registry_module, "_canonical_json", hash_with_swap)
    with pytest.raises(ValueError, match="registry binding"):
        registry.bind(call)
    assert reached == ["bound-hash"]
    assert backend.calls == 0


def test_unchanged_call_keeps_stable_bound_identity_without_dispatch():
    registry, call, entry, backend = _fixture()
    assert registry.resolve(call) is entry
    first = registry.bind(call)
    second = registry.bind(call)
    assert first.call is second.call is call
    assert first.registration is second.registration is entry
    assert first.bound_action_id == second.bound_action_id
    assert first.registry_revision == second.registry_revision
    assert backend.calls == 0
