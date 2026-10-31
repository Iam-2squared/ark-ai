"""Retained READ receipt rechecking remains strictly disconnected and inert."""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.agency import disconnected_registered_read_recheck as recheck
from ark.agency.contracts import CapabilityGrant, Effect, ToolCall
from ark.agency.disconnected_registered_read_preflight import (
    DisconnectedReadPreflight,
    review_disconnected_registered_read,
)
from ark.agency.policy import PermissionGate
from ark.agency.registry import ToolRegistration, ToolRegistry


class _ForbiddenBackend:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("no detached receipt reviewer may dispatch")


def _fixture(effect: Effect = Effect.READ):
    backend = _ForbiddenBackend()
    registry = ToolRegistry((
        ToolRegistration("local.inspect", "local.inspect", effect, "mock:01", backend),
    ))
    gate = PermissionGate()
    call = ToolCall(
        "local.inspect", "local.inspect", "user:fixture", {"key": "secret"},
    )
    grant = CapabilityGrant("local.inspect", "user:fixture", 200)
    return registry, gate, call, grant, backend


def _receipt(registry, gate, call, grant, *, now=100):
    return review_disconnected_registered_read(
        registry, gate, call, (grant,), now_ms=now,
    )


def test_matching_retained_read_receipt_is_a_noop() -> None:
    registry, gate, call, grant, backend = _fixture()
    receipt = _receipt(registry, gate, call, grant)
    assert recheck.verify_disconnected_registered_read_receipt(
        receipt, registry, gate, call, (grant,), now_ms=100,
    ) is None
    assert backend.calls == 0
    assert not gate._consumed_tokens
    assert "secret" not in repr(receipt)


def test_repeated_check_does_not_consume_any_grant_or_run_backend() -> None:
    registry, gate, call, grant, backend = _fixture()
    receipt = _receipt(registry, gate, call, grant)
    for _ in range(3):
        recheck.verify_disconnected_registered_read_receipt(
            receipt, registry, gate, call, (grant,), now_ms=100,
        )
    assert backend.calls == 0
    assert gate._consumed_tokens == set()


@pytest.mark.parametrize(
    "field,value",
    (
        ("registry_revision", "tools_" + "0" * 64),
        ("bound_action_id", "bound_" + "0" * 64),
        ("request_id", "act_" + "0" * 64),
        ("tool_name", "different"),
        ("capability", "different"),
    ),
)
def test_retained_receipt_field_substitution_is_rejected(
    field: str, value: str,
) -> None:
    registry, gate, call, grant, backend = _fixture()
    receipt = replace(_receipt(registry, gate, call, grant), **{field: value})
    with pytest.raises(recheck.DisconnectedReadReceiptRejected, match="differs"):
        recheck.verify_disconnected_registered_read_receipt(
            receipt, registry, gate, call, (grant,), now_ms=100,
        )
    assert backend.calls == 0


def test_expired_grant_does_not_replay_old_read_receipt() -> None:
    registry, gate, call, grant, backend = _fixture()
    receipt = _receipt(registry, gate, call, grant, now=100)
    with pytest.raises(recheck.DisconnectedReadReceiptRejected, match="denied"):
        recheck.verify_disconnected_registered_read_receipt(
            receipt, registry, gate, call, (grant,), now_ms=201,
        )
    assert backend.calls == 0


def test_wrong_scope_cannot_reuse_original_read_receipt() -> None:
    registry, gate, call, grant, backend = _fixture()
    receipt = _receipt(registry, gate, call, grant)
    other = CapabilityGrant("local.inspect", "user:other", 200)
    with pytest.raises(recheck.DisconnectedReadReceiptRejected, match="denied"):
        recheck.verify_disconnected_registered_read_receipt(
            receipt, registry, gate, call, (other,), now_ms=100,
        )
    assert backend.calls == 0


def test_write_registry_is_refused_before_gate_and_backend() -> None:
    read_registry, gate, call, grant, _ = _fixture()
    receipt = _receipt(read_registry, gate, call, grant)
    write_registry, _, _, _, backend = _fixture(Effect.WRITE)
    with pytest.raises(recheck.DisconnectedReadReceiptRejected, match="denied"):
        recheck.verify_disconnected_registered_read_receipt(
            receipt, write_registry, gate, call, (grant,), now_ms=100,
        )
    assert backend.calls == 0
    assert not gate._consumed_tokens


@pytest.mark.parametrize("bad_now", (True, -1, 2**63, 1.0, "100"))
def test_clock_is_exact_bounded_synthetic_input(bad_now: object) -> None:
    registry, gate, call, grant, _ = _fixture()
    receipt = _receipt(registry, gate, call, grant)
    with pytest.raises(recheck.DisconnectedReadReceiptRejected, match="exact bounded"):
        recheck.verify_disconnected_registered_read_receipt(
            receipt, registry, gate, call, (grant,), now_ms=bad_now,
        )


def test_exact_tuple_and_grant_budget_required() -> None:
    registry, gate, call, grant, _ = _fixture()
    receipt = _receipt(registry, gate, call, grant)
    for bad in ([grant], (object(),), (grant,) * 129):
        with pytest.raises(recheck.DisconnectedReadReceiptRejected, match="exact bounded"):
            recheck.verify_disconnected_registered_read_receipt(
                receipt, registry, gate, call, bad, now_ms=100,
            )


def test_non_receipt_objects_are_not_accepted() -> None:
    registry, gate, call, grant, _ = _fixture()
    for bad in (object(), None, {}):
        with pytest.raises(recheck.DisconnectedReadReceiptRejected, match="exact bounded"):
            recheck.verify_disconnected_registered_read_receipt(
                bad, registry, gate, call, (grant,), now_ms=100,
            )


def test_reflected_equal_value_call_swap_during_review_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry, gate, call, grant, backend = _fixture()
    receipt = _receipt(registry, gate, call, grant)
    original = recheck.review_disconnected_registered_read

    def changed(*args, **kwargs):
        result = original(*args, **kwargs)
        replacement = (" " + call.scope)[1:]
        assert replacement == call.scope and replacement is not call.scope
        object.__setattr__(call, "scope", replacement)
        return result

    monkeypatch.setattr(recheck, "review_disconnected_registered_read", changed)
    with pytest.raises(recheck.DisconnectedReadReceiptRejected, match="epoch changed"):
        recheck.verify_disconnected_registered_read_receipt(
            receipt, registry, gate, call, (grant,), now_ms=100,
        )
    assert backend.calls == 0


def test_reflected_grant_swap_after_preflight_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry, gate, call, grant, backend = _fixture()
    receipt = _receipt(registry, gate, call, grant)
    original = recheck.review_disconnected_registered_read

    def changed(*args, **kwargs):
        result = original(*args, **kwargs)
        replacement = (" " + grant.scope)[1:]
        assert replacement == grant.scope and replacement is not grant.scope
        object.__setattr__(grant, "scope", replacement)
        return result

    monkeypatch.setattr(recheck, "review_disconnected_registered_read", changed)
    with pytest.raises(recheck.DisconnectedReadReceiptRejected, match="epoch changed"):
        recheck.verify_disconnected_registered_read_receipt(
            receipt, registry, gate, call, (grant,), now_ms=100,
        )
    assert backend.calls == 0


def test_forged_fresh_receipt_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry, gate, call, grant, backend = _fixture()
    receipt = _receipt(registry, gate, call, grant)

    def forged(*args, **kwargs):
        return replace(receipt, bound_action_id="bound_" + "1" * 64)

    monkeypatch.setattr(recheck, "review_disconnected_registered_read", forged)
    with pytest.raises(recheck.DisconnectedReadReceiptRejected, match="differs"):
        recheck.verify_disconnected_registered_read_receipt(
            receipt, registry, gate, call, (grant,), now_ms=100,
        )
    assert backend.calls == 0


def test_authority_flag_property_cannot_turn_receipt_into_permission(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry, gate, call, grant, backend = _fixture()
    receipt = _receipt(registry, gate, call, grant)
    monkeypatch.setattr(
        DisconnectedReadPreflight, "external_read_authorized",
        property(lambda self: True),
    )
    with pytest.raises(recheck.DisconnectedReadReceiptRejected, match="epoch changed"):
        recheck.verify_disconnected_registered_read_receipt(
            receipt, registry, gate, call, (grant,), now_ms=100,
        )
    assert backend.calls == 0
