"""Run1403: ToolRegistration class lookup-hook absence is pinned exactly."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import pytest

import ark.agency.registry as registry_module
from ark.agency.contracts import Effect
from ark.agency.registry import ToolRegistration


class _NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: object) -> object:
        self.calls += 1
        raise AssertionError("registration custody tests must never dispatch")


def _registration() -> tuple[ToolRegistration, _NeverExecute]:
    backend = _NeverExecute()
    entry = ToolRegistration(
        "fixture.read",
        "fixture.read",
        Effect.READ,
        "disconnected.mock.v1",
        backend,
    )
    return entry, backend


@contextmanager
def _class_attribute(
    carrier: type,
    name: str,
    value: object,
) -> Iterator[None]:
    namespace = vars(carrier)
    was_present = name in namespace
    original = namespace.get(name)
    type.__setattr__(carrier, name, value)
    try:
        yield
    finally:
        if was_present:
            type.__setattr__(carrier, name, original)
        else:
            type.__delattr__(carrier, name)


@pytest.mark.parametrize("hook", ("__new__", "__getattribute__", "__getattr__"))
def test_explicit_none_is_not_confused_with_an_absent_registration_hook(
    hook: str,
) -> None:
    _entry, backend = _registration()

    with _class_attribute(ToolRegistration, hook, None):
        with pytest.raises(
            ValueError,
            match="tool registration contract changed",
        ):
            registry_module._require_original_registration_contract()

    registry_module._require_original_registration_contract()
    assert backend.calls == 0


def test_exact_absence_sentinel_installed_as_a_hook_is_rejected() -> None:
    _entry, backend = _registration()

    with _class_attribute(
        ToolRegistration,
        "__getattr__",
        registry_module._REGISTRATION_HOOK_ABSENT,
    ):
        with pytest.raises(
            ValueError,
            match="tool registration contract changed",
        ):
            registry_module._require_original_registration_contract()

    assert backend.calls == 0


def test_replaced_absence_sentinel_is_rejected_before_registration_reads(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _entry, backend = _registration()

    with monkeypatch.context() as patch:
        patch.setattr(registry_module, "_REGISTRATION_HOOK_ABSENT", object())
        with pytest.raises(
            ValueError,
            match="tool registration contract changed",
        ):
            registry_module._require_original_registration_contract()

    assert backend.calls == 0


def test_equal_valued_replacement_hook_name_vector_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _entry, backend = _registration()
    replacement = tuple(list(registry_module._REGISTRATION_HOOKS))
    assert replacement == registry_module._REGISTRATION_HOOKS
    assert replacement is not registry_module._REGISTRATION_HOOKS

    with monkeypatch.context() as patch:
        patch.setattr(registry_module, "_REGISTRATION_HOOKS", replacement)
        with pytest.raises(
            ValueError,
            match="tool registration contract changed",
        ):
            registry_module._require_original_registration_contract()

    assert backend.calls == 0


def test_exact_registration_class_still_passes_without_backend_execution() -> None:
    _entry, backend = _registration()

    registry_module._require_original_registration_contract()

    assert backend.calls == 0
