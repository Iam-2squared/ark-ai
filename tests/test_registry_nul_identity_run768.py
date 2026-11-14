"""Registry identities reject NUL before a backend descriptor is inspected.

The backend here is synthetic and never invoked.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("registered backend must not run")


class DescriptorTrap:
    @property
    def execute(self) -> object:
        raise AssertionError("backend descriptor must not be read")


@pytest.mark.parametrize("field", ("name", "capability", "backend_id"))
def test_nul_registration_identity_rejected_before_backend_inspection(
    field: str,
) -> None:
    values: dict[str, object] = {
        "name": "mock.writer",
        "capability": "mock.write",
        "effect": Effect.WRITE,
        "backend_id": "local",
        "backend": DescriptorTrap(),
    }
    values[field] = "safe" + chr(0) + "trailer"
    with pytest.raises(ValueError, match="NUL separator"):
        ToolRegistration(**values)


def test_unicode_registry_identity_remains_stable_and_never_executes() -> None:
    backend = NeverExecute()
    item = ToolRegistration(
        "fixture.検索", "local.試験", Effect.READ, "offline.検証", backend,
    )
    registry = ToolRegistry((item,))
    call = ToolCall(item.name, item.capability, "fixture.local", {})
    assert registry.resolve(call) is item
    assert registry.revision == ToolRegistry((item,)).revision
    assert backend.calls == 0
