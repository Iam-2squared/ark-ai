"""Run1405: startup carrier hook absence is distinguished from None."""

from __future__ import annotations

import pytest

import ark.startup_readiness_review as readiness


_CARRIERS = (
    "StartupComponent",
    "ComponentResult",
    "StartupSnapshot",
)
_HOOKS = ("__new__", "__getattribute__", "__getattr__")


@pytest.mark.parametrize("carrier_name", _CARRIERS)
@pytest.mark.parametrize("hook", _HOOKS)
def test_explicit_none_is_not_confused_with_an_absent_startup_hook(
    monkeypatch: pytest.MonkeyPatch,
    carrier_name: str,
    hook: str,
) -> None:
    carrier = getattr(readiness, carrier_name)

    with monkeypatch.context() as patch:
        patch.setattr(carrier, hook, None, raising=False)
        with pytest.raises(
            ValueError,
            match="startup constructor authority changed",
        ):
            readiness._assert_original_startup_constructors()


def test_exact_absence_sentinel_installed_as_a_hook_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(
            readiness.StartupComponent,
            "__getattr__",
            readiness._STARTUP_CARRIER_HOOK_ABSENT,
            raising=False,
        )
        with pytest.raises(
            ValueError,
            match="startup constructor authority changed",
        ):
            readiness._assert_original_startup_constructors()


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

    with monkeypatch.context() as patch:
        patch.setattr(
            readiness.StartupComponent,
            "__getattribute__",
            forbidden,
            raising=False,
        )
        with pytest.raises(
            ValueError,
            match="startup constructor authority changed",
        ):
            readiness.evaluate_startup_readiness(probes())

    assert invoked == []
    assert consumed == []


def test_original_startup_carrier_hooks_remain_available() -> None:
    readiness._assert_original_startup_constructors()
