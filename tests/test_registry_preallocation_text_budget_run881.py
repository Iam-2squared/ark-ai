"""Bound registry names before backend inspection or linear text scanning."""
import pytest

from ark.agency import registry as registry_module
from ark.agency.contracts import Effect


class _DisconnectedBackend:
    def execute(self, call: object) -> object:
        raise AssertionError("backend must never execute")


@pytest.mark.parametrize("field", ["name", "capability", "backend_id"])
@pytest.mark.parametrize("value", ["x" * 257, " " * 257])
def test_oversized_registration_identity_denied_before_backend_probe(
    monkeypatch: pytest.MonkeyPatch, field: str, value: str,
) -> None:
    def unexpected_probe(backend: object) -> object:
        raise AssertionError("invalid registry identity reached backend inspection")

    monkeypatch.setattr(
        registry_module, "_backend_execute_descriptor", unexpected_probe,
    )
    data: dict[str, object] = {
        "name": "local.read", "capability": "local.read",
        "effect": Effect.READ, "backend_id": "local.mock",
        "backend": _DisconnectedBackend(),
    }
    data[field] = value
    with pytest.raises(ValueError, match="registry identifier budget"):
        registry_module.ToolRegistration(**data)


def test_registry_utf8_boundary_accepts_exact_256_bytes() -> None:
    registration = registry_module.ToolRegistration(
        name="é" * 128, capability="local.read", effect=Effect.READ,
        backend_id="local.mock", backend=_DisconnectedBackend(),
    )
    assert len(registration.name.encode("utf-8")) == 256
