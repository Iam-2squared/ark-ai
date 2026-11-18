"""Run969: detached registry identities reject invisible alias scalars.

No backend execution or external effect. Frozen ToolCall v1 is unchanged.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry

_INVISIBLE_SCALARS = (
    0x00AD, 0x034F, 0x180E, 0x200B, 0x200C, 0x200D,
    0x2060, 0x2061, 0x2062, 0x2063, 0x2064, 0xFEFF,
    0x206A, 0x206B, 0x206C, 0x206D, 0x206E, 0x206F,
)


class _MockBackend:
    def execute(self, _call: ToolCall) -> str:
        raise AssertionError("inert registry tests must not execute backends")


@pytest.mark.parametrize("codepoint", _INVISIBLE_SCALARS)
@pytest.mark.parametrize("field", ("name", "capability", "backend_id"))
def test_invisible_registration_identity_denied_before_registry_creation(codepoint, field):
    values = {
        "name": "mock.read",
        "capability": "read",
        "backend_id": "local.mock",
    }
    values[field] = "safe" + chr(codepoint) + "alias"
    with pytest.raises(ValueError, match="Unicode formatting control"):
        ToolRegistration(
            values["name"], values["capability"], Effect.READ,
            values["backend_id"], _MockBackend(),
        )


@pytest.mark.parametrize("codepoint", _INVISIBLE_SCALARS)
@pytest.mark.parametrize("operation", ("resolve", "bind"))
def test_invisible_permission_scope_denied_before_binding(codepoint, operation):
    registry = ToolRegistry((
        ToolRegistration("mock.read", "read", Effect.READ, "local.mock", _MockBackend()),
    ))
    call = ToolCall("mock.read", "read", "local" + chr(codepoint))
    with pytest.raises(ValueError, match="Unicode formatting control"):
        getattr(registry, operation)(call)


def test_multilingual_registry_labels_and_scope_remain_usable():
    registry = ToolRegistry((
        ToolRegistration("検索", "情報", Effect.READ, "端末ローカル", _MockBackend()),
    ))
    call = ToolCall("検索", "情報", "東京/端末")
    assert registry.resolve(call).name == "検索"
    assert registry.bind(call).registration.name == "検索"
