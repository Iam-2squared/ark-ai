"""Run1406: atomic pre-action carriers pin absent class hooks exactly."""

from __future__ import annotations

import pytest
from ark.agency import disconnected_atomic_preaction_ledger as atomic


_CARRIERS = (
    "AtomicIntentClaim",
    "AtomicPreactionWitness",
    "AtomicPreactionSnapshot",
)
_HOOKS = ("__new__", "__getattribute__", "__getattr__")


def _set_class_attribute(
    carrier: type,
    name: str,
    value: object,
) -> tuple[bool, object | None]:
    namespace = vars(carrier)
    was_present = name in namespace
    original = namespace.get(name)
    type.__setattr__(carrier, name, value)
    return was_present, original


def _restore_class_attribute(
    carrier: type,
    name: str,
    original: tuple[bool, object | None],
) -> None:
    was_present, value = original
    if was_present:
        type.__setattr__(carrier, name, value)
    else:
        type.__delattr__(carrier, name)


@pytest.mark.parametrize("carrier_name", _CARRIERS)
@pytest.mark.parametrize("hook", _HOOKS)
def test_explicit_none_is_not_confused_with_absent_carrier_hook(
    carrier_name: str,
    hook: str,
) -> None:
    carrier = getattr(atomic, carrier_name)
    original = _set_class_attribute(carrier, hook, None)
    try:
        with pytest.raises(
            atomic.AtomicPreactionRejected,
            match="carrier definition changed",
        ):
            atomic._require_original_atomic_carriers()
    finally:
        _restore_class_attribute(carrier, hook, original)


def test_exact_absence_sentinel_installed_as_carrier_hook_is_rejected() -> None:
    hook = "__getattr__"
    original = _set_class_attribute(
        atomic.AtomicIntentClaim,
        hook,
        atomic._CARRIER_HOOK_ABSENT,
    )
    try:
        with pytest.raises(
            atomic.AtomicPreactionRejected,
            match="carrier definition changed",
        ):
            atomic._require_original_atomic_carriers()
    finally:
        _restore_class_attribute(atomic.AtomicIntentClaim, hook, original)


def test_replaced_carrier_absence_sentinel_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(atomic, "_CARRIER_HOOK_ABSENT", object())
    with pytest.raises(
        atomic.AtomicPreactionRejected,
        match="carrier definition changed",
    ):
        atomic._require_original_atomic_carriers()


def test_equal_valued_carrier_hook_vector_replacement_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    replacement = tuple(list(atomic._CARRIER_HOOKS))
    assert replacement == atomic._CARRIER_HOOKS
    assert replacement is not atomic._CARRIER_HOOKS

    monkeypatch.setattr(atomic, "_CARRIER_HOOKS", replacement)
    with pytest.raises(
        atomic.AtomicPreactionRejected,
        match="carrier definition changed",
    ):
        atomic._require_original_atomic_carriers()


def test_snapshot_false_still_skips_only_the_snapshot_carrier() -> None:
    hook = "__getattr__"
    original = _set_class_attribute(
        atomic.AtomicPreactionSnapshot,
        hook,
        None,
    )
    try:
        atomic._require_original_atomic_carriers(snapshot=False)
        with pytest.raises(
            atomic.AtomicPreactionRejected,
            match="carrier definition changed",
        ):
            atomic._require_original_atomic_carriers()
    finally:
        _restore_class_attribute(
            atomic.AtomicPreactionSnapshot, hook, original,
        )


@pytest.mark.parametrize("hook", _HOOKS)
def test_ledger_explicit_none_is_not_confused_with_absent_hook(hook: str) -> None:
    ledger = object.__new__(atomic.DisconnectedAtomicPreactionLedger)
    original = _set_class_attribute(
        atomic.DisconnectedAtomicPreactionLedger, hook, None,
    )
    try:
        with pytest.raises(
            atomic.AtomicPreactionRejected,
            match="implementation changed",
        ):
            atomic._require_ledger_path_epoch(ledger)
    finally:
        _restore_class_attribute(
            atomic.DisconnectedAtomicPreactionLedger, hook, original,
        )


def test_exact_absence_sentinel_installed_as_ledger_hook_is_rejected() -> None:
    ledger = object.__new__(atomic.DisconnectedAtomicPreactionLedger)
    hook = "__getattr__"
    original = _set_class_attribute(
        atomic.DisconnectedAtomicPreactionLedger,
        hook,
        atomic._LEDGER_HOOK_ABSENT,
    )
    try:
        with pytest.raises(
            atomic.AtomicPreactionRejected,
            match="implementation changed",
        ):
            atomic._require_ledger_path_epoch(ledger)
    finally:
        _restore_class_attribute(
            atomic.DisconnectedAtomicPreactionLedger, hook, original,
        )


def test_replaced_ledger_absence_sentinel_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    ledger = object.__new__(atomic.DisconnectedAtomicPreactionLedger)
    monkeypatch.setattr(atomic, "_LEDGER_HOOK_ABSENT", object())
    with pytest.raises(
        atomic.AtomicPreactionRejected,
        match="implementation changed",
    ):
        atomic._require_ledger_path_epoch(ledger)


def test_hostile_ledger_lookup_hook_is_rejected_before_instance_access() -> None:
    invoked: list[str] = []
    ledger = object.__new__(atomic.DisconnectedAtomicPreactionLedger)

    def forbidden(_self: object, _name: str) -> object:
        invoked.append("lookup")
        raise AssertionError("substituted ledger lookup hook executed")

    original = _set_class_attribute(
        atomic.DisconnectedAtomicPreactionLedger,
        "__getattribute__",
        forbidden,
    )
    try:
        with pytest.raises(
            atomic.AtomicPreactionRejected,
            match="implementation changed",
        ):
            atomic._require_ledger_path_epoch(ledger)
    finally:
        _restore_class_attribute(
            atomic.DisconnectedAtomicPreactionLedger,
            "__getattribute__",
            original,
        )

    assert invoked == []


def test_clean_atomic_preaction_ledger_path_contract_remains_valid(tmp_path) -> None:
    ledger = atomic.DisconnectedAtomicPreactionLedger.create(
        tmp_path / "atomic-preaction-hook-custody.sqlite3",
    )

    assert atomic._require_ledger_path_epoch(ledger) == ledger._path
    assert not hasattr(ledger, "execute")
