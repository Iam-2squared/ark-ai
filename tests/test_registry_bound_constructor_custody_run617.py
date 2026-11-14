"""A detached ToolRegistry must never invoke an untrusted bound constructor.

No mock backend is executed, and the bound request is not an approval token.
"""

import pytest

from ark.agency import registry as registry_module
from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, _request):
        self.calls += 1
        raise AssertionError("registry binding must not dispatch tools")


def _fixture():
    backend = NeverExecute()
    entry = ToolRegistration(
        "offline.write", "fixture.write", Effect.WRITE, "offline-only", backend,
    )
    registry = ToolRegistry((entry,))
    call = ToolCall("offline.write", "fixture.write", "local", {"x": 1})
    return backend, registry, call


@pytest.mark.parametrize("epoch", ("preinstalled", "bound_hash_callback"))
def test_rebound_original_constructor_refused_without_execution(
    monkeypatch, epoch,
):
    backend, registry, call = _fixture()
    invoked = []

    def injected(self, *args, **kwargs):
        invoked.append((args, kwargs))
        raise AssertionError("untrusted bound constructor executed")

    if epoch == "preinstalled":
        monkeypatch.setattr(registry_module.BoundAction, "__init__", injected)
    else:
        original_sha256 = registry_module.hashlib.sha256

        def inject_during_bound_digest(payload=b""):
            if b'"registry_revision"' in payload:
                monkeypatch.setattr(
                    registry_module.BoundAction, "__init__", injected,
                )
            return original_sha256(payload)

        monkeypatch.setattr(
            registry_module.hashlib, "sha256", inject_during_bound_digest,
        )

    expected_denial = (
        "bound result constructor changed" if epoch == "preinstalled"
        else "registry digest dependencies changed"
    )
    with pytest.raises(ValueError, match=expected_denial):
        registry.bind(call)
    assert invoked == []
    assert backend.calls == 0


def test_import_rebound_result_class_is_refused_before_constructor(monkeypatch):
    backend, registry, call = _fixture()
    invoked = []

    class CounterfeitBound:
        def __init__(self, **kwargs):
            invoked.append(kwargs)
            raise AssertionError("untrusted class constructor executed")

    monkeypatch.setattr(registry_module, "BoundAction", CounterfeitBound)
    with pytest.raises(ValueError, match="bound result constructor changed"):
        registry.bind(call)
    assert invoked == []
    assert backend.calls == 0


def test_original_registry_binding_remains_deterministic_and_non_authorizing():
    backend, registry, call = _fixture()
    one = registry.bind(call)
    two = registry.bind(call)
    assert type(one) is registry_module.BoundAction
    assert one.bound_action_id == two.bound_action_id
    assert one.call is call
    assert one.registration is registry.get(call.tool)
    assert backend.calls == 0
