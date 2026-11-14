"""Static ToolRegistry backend introspection must never call a swapped inspector.

These are inert local fixture backends; no ToolBackend execution, grants,
consent, real-world action, or persistent approval is involved.
"""

import pytest

import ark.agency.registry as registry_module
from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class Backend:
    def __init__(self):
        self.dispatches = 0

    def execute(self, _call):
        self.dispatches += 1
        raise AssertionError("no backend should ever be executed")


def _registration(backend):
    return ToolRegistration(
        "fixture.read", "fixture.read", Effect.READ, "offline.fixture", backend,
    )


def _fixture():
    backend = Backend()
    item = _registration(backend)
    registry = ToolRegistry((item,))
    call = ToolCall("fixture.read", "fixture.read", "synthetic.private")
    return backend, item, registry, call


@pytest.mark.parametrize("replacement", ("getattr_static", "inspect_module"))
@pytest.mark.parametrize("route", ("register", "revision", "resolve", "bind"))
def test_substituted_inspection_refused_before_backend_introspection(
    monkeypatch, replacement, route,
):
    backend, _registration_value, registry, call = _fixture()
    called = []

    def hostile(*_args, **_kwargs):
        called.append("forged static inspector executed")
        raise AssertionError("unexpected backend descriptor access")

    with monkeypatch.context() as patch:
        if replacement == "getattr_static":
            patch.setattr(registry_module.inspect, "getattr_static", hostile)
        else:
            patch.setattr(registry_module, "inspect", object())
        if route == "register":
            with pytest.raises(TypeError, match="static inspection dependency changed"):
                _registration(backend)
        else:
            with pytest.raises(ValueError, match="backend execute interface changed"):
                if route == "revision":
                    _ = registry.revision
                elif route == "resolve":
                    registry.resolve(call)
                else:
                    registry.bind(call)

    assert called == []
    assert backend.dispatches == 0


def test_generator_cannot_rebind_static_inspection_between_entries(monkeypatch):
    backend, item, _registry, _call = _fixture()
    other = ToolRegistration(
        "fixture.other", "fixture.other", Effect.READ, "offline.other", backend,
    )
    called = []
    advanced = []

    def hostile(*_args, **_kwargs):
        called.append("inspected")
        raise AssertionError("forged inspector ran")

    with monkeypatch.context() as patch:
        def changing_entries():
            yield item
            advanced.append("inspector replaced")
            patch.setattr(registry_module.inspect, "getattr_static", hostile)
            yield other
            advanced.append("consumed second entry")

        with pytest.raises(
            ValueError, match="registered tool changed during registry construction",
        ):
            ToolRegistry(changing_entries())

    assert advanced == ["inspector replaced"]
    assert called == []
    assert backend.dispatches == 0


def test_unchanged_static_inspection_retains_deterministic_registry_identity():
    backend, registration, registry, call = _fixture()
    first = registry.bind(call)
    second = registry.bind(call)
    assert first.registration is second.registration is registration
    assert first.bound_action_id == second.bound_action_id
    assert registry.revision == first.registry_revision
    assert backend.dispatches == 0
