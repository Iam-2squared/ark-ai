"""Run1405: startup carrier hook absence is distinguished from None."""

from __future__ import annotations

import subprocess
import sys

import pytest

import ark.startup_readiness_review as readiness

_CARRIERS = (
    "StartupComponent",
    "ComponentResult",
    "StartupSnapshot",
)
_HOOKS = ("__getattribute__", "__getattr__")


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
def test_explicit_none_is_not_confused_with_an_absent_startup_hook(
    carrier_name: str,
    hook: str,
) -> None:
    carrier = getattr(readiness, carrier_name)

    original = _set_class_attribute(carrier, hook, None)
    try:
        with pytest.raises(
            ValueError,
            match="startup constructor authority changed",
        ):
            readiness._assert_original_startup_constructors()
    finally:
        _restore_class_attribute(carrier, hook, original)



@pytest.mark.parametrize("carrier_name", _CARRIERS)
def test_explicit_none_new_hook_is_rejected_in_an_isolated_process(
    carrier_name: str,
) -> None:
    # Mutating a special __new__ slot and deleting it can leave interpreter
    # allocation state behind on some Python builds. Keep this probe isolated.
    script = f"""
import ark.startup_readiness_review as readiness

carrier = getattr(readiness, {carrier_name!r})
type.__setattr__(carrier, "__new__", None)
try:
    readiness._assert_original_startup_constructors()
except ValueError:
    pass
else:
    raise SystemExit("explicit None __new__ hook was accepted")
"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout

def test_exact_absence_sentinel_installed_as_a_hook_is_rejected() -> None:
    hook = "__getattr__"
    original = _set_class_attribute(
        readiness.StartupComponent,
        hook,
        readiness._STARTUP_CARRIER_HOOK_ABSENT,
    )
    try:
        with pytest.raises(
            ValueError,
            match="startup constructor authority changed",
        ):
            readiness._assert_original_startup_constructors()
    finally:
        _restore_class_attribute(readiness.StartupComponent, hook, original)


def test_replaced_absence_sentinel_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(readiness, "_STARTUP_CARRIER_HOOK_ABSENT", object())
        with pytest.raises(
            ValueError,
            match="startup constructor authority changed",
        ):
            readiness._assert_original_startup_constructors()


def test_equal_valued_hook_name_vector_replacement_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    replacement = tuple(list(readiness._STARTUP_CARRIER_HOOKS))
    assert replacement == readiness._STARTUP_CARRIER_HOOKS
    assert replacement is not readiness._STARTUP_CARRIER_HOOKS

    with monkeypatch.context() as patch:
        patch.setattr(readiness, "_STARTUP_CARRIER_HOOKS", replacement)
        with pytest.raises(
            ValueError,
            match="startup constructor authority changed",
        ):
            readiness._assert_original_startup_constructors()


def test_hostile_lookup_hook_is_rejected_before_probe_iteration(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoked: list[str] = []
    consumed: list[bool] = []

    def forbidden(_self: object, _name: str) -> object:
        invoked.append("lookup")
        raise AssertionError("substituted startup lookup hook executed")

    def probes():
        consumed.append(True)
        yield readiness.StartupComponent(
            "memory",
            schema_revision="memory-v1",
        )

    hook = "__getattribute__"
    original = _set_class_attribute(
        readiness.StartupComponent, hook, forbidden,
    )
    try:
        with pytest.raises(
            ValueError,
            match="startup constructor authority changed",
        ):
            readiness.evaluate_startup_readiness(probes())
    finally:
        _restore_class_attribute(readiness.StartupComponent, hook, original)

    assert invoked == []
    assert consumed == []


def test_original_startup_carrier_hooks_remain_available() -> None:
    readiness._assert_original_startup_constructors()
