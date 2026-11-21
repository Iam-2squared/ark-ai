"""Detached Planner restart protocol must refuse executable equality at ingress.

All fixtures are local, inert and non-authorizing. No SQLite or backend is opened.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ark.agency import disconnected_planner_slot_restart_bridge as bridge


@pytest.mark.parametrize("injection", ("descriptor", "codec", "reviewer"))
def test_protocol_rejects_hostile_equality_without_invocation(
    monkeypatch: pytest.MonkeyPatch, injection: str,
) -> None:
    calls: list[str] = []

    class Hostile:
        def __call__(self, *_args: object, **_kwargs: object) -> object:
            calls.append("call")
            raise AssertionError("untrusted callback ran")

        def __eq__(self, _other: object) -> bool:
            calls.append("eq")
            raise AssertionError("untrusted equality ran")

        def __ne__(self, _other: object) -> bool:
            calls.append("ne")
            raise AssertionError("untrusted inequality ran")

    with monkeypatch.context() as patch:
        if injection == "descriptor":
            patch.setattr(bridge.DisconnectedDependencyClaim, "__init__", Hostile())
        elif injection == "codec":
            patch.setattr(bridge, "hashlib", SimpleNamespace(sha256=Hostile()))
        else:
            patch.setattr(
                bridge.bundle_module,
                "review_disconnected_restart_receipt_bundle",
                Hostile(),
            )
        with pytest.raises(
            bridge.DisconnectedPlannerSlotBridgeRejected,
            match="restart bridge protocol changed",
        ):
            bridge._protocol()
    assert calls == []


def test_unmodified_restart_bridge_protocol_remains_available() -> None:
    # A passing local callback-custody check is NOT a persisted Planner receipt,
    # independent source attestation, replay permission or dispatch authority.
    bridge._protocol()
