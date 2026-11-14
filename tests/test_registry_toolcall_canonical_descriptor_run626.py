"""ToolRegistry must not invoke replaced ToolCall identity machinery.

No mock backend is ever dispatched, and registry binding is not permission
to perform an external action.
"""

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NeverExecute:
    def __init__(self):
        self.calls = 0

    def execute(self, _call):
        self.calls += 1
        raise AssertionError("registry must not execute a tool")


def _case():
    backend = _NeverExecute()
    registration = ToolRegistration(
        "fixture.read", "cap.read", Effect.READ, "offline", backend,
    )
    registry = ToolRegistry((registration,))
    call = ToolCall("fixture.read", "cap.read", "local", {"k": 1})
    return backend, registry, call, registration


@pytest.mark.parametrize("operation", ("resolve", "bind"))
@pytest.mark.parametrize(
    "member", ("__init__", "__post_init__", "request_id", "arguments_sha256"),
)
def test_preinstalled_identity_code_is_rejected_before_invocation(
    monkeypatch, operation, member,
):
    backend, registry, call, _ = _case()
    invoked = []

    def forbidden(*_args, **_kwargs):
        invoked.append(member)
        raise AssertionError("forged ToolCall member must never run")

    with monkeypatch.context() as patch:
        replacement = (
            property(forbidden) if member in ("request_id", "arguments_sha256")
            else forbidden
        )
        patch.setattr(ToolCall, member, replacement)
        with pytest.raises(ValueError, match="ToolCall identity constructor changed"):
            getattr(registry, operation)(call)

    assert invoked == []
    assert backend.calls == 0


@pytest.mark.parametrize("operation", ("resolve", "bind"))
@pytest.mark.parametrize("member", ("__post_init__", "request_id"))
def test_lookup_callback_cannot_install_identity_code(
    monkeypatch, operation, member,
):
    backend, registry, call, _ = _case()
    invoked = []
    get_original = registry.get

    def forbidden(*_args, **_kwargs):
        invoked.append(member)
        raise AssertionError("forged ToolCall member must never run")

    with monkeypatch.context() as patch:
        def install_at_lookup(name):
            result = get_original(name)
            replacement = property(forbidden) if member == "request_id" else forbidden
            patch.setattr(ToolCall, member, replacement)
            return result

        patch.setattr(registry, "get", install_at_lookup)
        with pytest.raises(ValueError, match="ToolCall identity constructor changed"):
            getattr(registry, operation)(call)

    assert invoked == []
    assert backend.calls == 0


@pytest.mark.parametrize("operation", ("resolve", "bind"))
def test_original_toolcall_is_an_inert_registry_binding(operation):
    backend, registry, call, registration = _case()
    result = getattr(registry, operation)(call)
    if operation == "resolve":
        assert result is registration
    else:
        assert result.registration is registration
        assert result.call is call
        assert result.registry_revision == registry.revision
    assert backend.calls == 0
