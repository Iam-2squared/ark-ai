"""Run1389: proactive policy/state validators retain original vectors."""

from __future__ import annotations

import pytest

import ark.proactive_state_ledger as ledger_module
from ark.proactive_state_ledger import (
    SyntheticProactivePolicy,
    SyntheticProactiveState,
    SyntheticProactiveStateRejected,
)


def _policy() -> SyntheticProactivePolicy:
    return SyntheticProactivePolicy(
        owner="owner-a",
        namespace="personal",
        definition_id="daily-summary",
        revision=1,
        policy_revision="policy-v1",
        minimum_interval_ms=100,
        cooldown_ms=200,
        rolling_window_ms=1000,
        max_previews_per_window=2,
    )


def test_joint_policy_vectors_are_rejected_before_descriptor_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    policy = _policy()
    invoked: list[str] = []
    empty: tuple[object, ...] = ()
    monkeypatch.setattr(ledger_module, "_POLICY_FIELDS", empty)
    monkeypatch.setattr(ledger_module, "_POLICY_METHODS", empty)
    monkeypatch.setattr(ledger_module, "_ORIGINAL_POLICY_FIELDS", empty)
    monkeypatch.setattr(ledger_module, "_ORIGINAL_POLICY_METHODS", empty)
    monkeypatch.setattr(
        ledger_module, "_ORIGINAL_POLICY_VECTORS", (empty, empty),
    )
    monkeypatch.setattr(
        SyntheticProactivePolicy,
        "owner",
        property(lambda _instance: (invoked.append("owner"), "owner-a")[1]),
    )

    with pytest.raises(SyntheticProactiveStateRejected, match="protocol changed"):
        policy.identity()

    assert invoked == []


def test_joint_state_vectors_are_rejected_before_descriptor_access(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    empty: tuple[object, ...] = ()
    monkeypatch.setattr(ledger_module, "_STATE_FIELDS", empty)
    monkeypatch.setattr(ledger_module, "_STATE_DENIALS", empty)
    monkeypatch.setattr(ledger_module, "_STATE_HOOKS", empty)
    monkeypatch.setattr(ledger_module, "_ORIGINAL_STATE_FIELDS", empty)
    monkeypatch.setattr(ledger_module, "_ORIGINAL_STATE_DENIALS", empty)
    monkeypatch.setattr(ledger_module, "_ORIGINAL_STATE_HOOKS", empty)
    monkeypatch.setattr(
        ledger_module, "_ORIGINAL_STATE_VECTORS", (empty, empty, empty),
    )
    invoked: list[str] = []

    def hostile_setter(_instance: object, _value: object) -> None:
        invoked.append("scope_digest")

    monkeypatch.setattr(
        SyntheticProactiveState,
        "scope_digest",
        property(
            lambda _instance: (invoked.append("scope_digest"), "a" * 64)[1],
            hostile_setter,
        ),
    )
    values = (
        "a" * 64,
        "b" * 64,
        1,
        "c" * 64,
        1,
        1,
        1,
        (1,),
        "ELIGIBLE_PREVIEW",
        1,
    )

    with pytest.raises(SyntheticProactiveStateRejected, match="protocol changed"):
        ledger_module._build_state(values)

    assert invoked == []


def test_protocol_rejects_joint_vectors_on_non_policy_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    empty: tuple[object, ...] = ()
    monkeypatch.setattr(ledger_module, "_POLICY_FIELDS", empty)
    monkeypatch.setattr(ledger_module, "_POLICY_METHODS", empty)
    monkeypatch.setattr(ledger_module, "_ORIGINAL_POLICY_FIELDS", empty)
    monkeypatch.setattr(ledger_module, "_ORIGINAL_POLICY_METHODS", empty)
    monkeypatch.setattr(
        ledger_module, "_ORIGINAL_POLICY_VECTORS", (empty, empty),
    )

    with pytest.raises(SyntheticProactiveStateRejected, match="protocol changed"):
        ledger_module._hash("ARK-test", ())
