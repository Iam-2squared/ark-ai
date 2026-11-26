"""Registry-bound synthetic WRITE intents enforce exact bounded occurrence IDs.

No ToolBackend, real permission, or real-world operation is invoked.
"""

from __future__ import annotations

import pytest

from ark.agency.contracts import Effect, ToolCall
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicPreactionRejected,
)
from ark.agency.disconnected_atomic_registry_bridge import (
    derive_registered_atomic_intent,
)
from ark.agency.registry import ToolRegistration, ToolRegistry


class NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("a registry intent must not execute a backend")


def _registry() -> tuple[ToolRegistry, ToolCall, NeverExecute]:
    backend = NeverExecute()
    registry = ToolRegistry((
        ToolRegistration(
            "writer", "fixture.write", Effect.WRITE, "local:fixture", backend,
        ),
    ))
    call = ToolCall("writer", "fixture.write", "local:fixture", {"n": 1})
    return registry, call, backend


@pytest.mark.parametrize(
    "occurrence_id", (
        "occ_" + "a" * 63,
        "occ_" + "a" * 65,
        "occ_" + "a" * 120_000,
        "occ_" + "A" * 64,
        "occ_" + "g" * 64,
        "slot_" + "a" * 64,
        "",
    ),
)
def test_malformed_or_oversized_occurrence_never_creates_registered_claim(
    occurrence_id: str,
) -> None:
    registry, call, backend = _registry()
    with pytest.raises(AtomicPreactionRejected, match="intent source"):
        derive_registered_atomic_intent(
            registry, call, occurrence_id=occurrence_id,
        )
    assert backend.calls == 0


def test_valid_registered_intent_is_still_denial_only() -> None:
    registry, call, backend = _registry()
    intent = derive_registered_atomic_intent(
        registry, call, occurrence_id="occ_" + "a" * 64,
    )
    assert intent.occurrence_id == "occ_" + "a" * 64
    assert intent.bound_action_id.startswith("bound_")
    assert len(intent.bound_action_id) == 70
    assert len(intent.request_sha256) == 64
    assert backend.calls == 0
