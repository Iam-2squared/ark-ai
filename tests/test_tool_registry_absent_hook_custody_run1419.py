"""Run1419: ToolRegistry pins true absence of allocation and lookup hooks."""

from __future__ import annotations

import subprocess
import sys

import pytest

import ark.agency.registry as registry_module
from ark.agency.contracts import Effect, ToolCall
from ark.agency.registry import ToolRegistration, ToolRegistry


class _NeverExecute:
    def __init__(self) -> None:
        self.calls = 0

    def execute(self, _call: ToolCall) -> object:
        self.calls += 1
        raise AssertionError("registry class-custody tests must never dispatch")


def _registry() -> tuple[ToolRegistry, _NeverExecute]:
    backend = _NeverExecute()
    registry = ToolRegistry((
        ToolRegistration(
            "fixture.read",
            "fixture.read",
            Effect.READ,
            "disconnected.mock.v1",
            backend,
        ),
    ))
    return registry, backend


def test_absent_registry_hooks_reject_none_and_exact_sentinel_in_subprocess() -> None:
    # __new__ can alter CPython type slots even after namespace restoration.
    # Keep every allocation/lookup-hook mutation in an isolated interpreter.
    script = r"""
import ark.agency.registry as registry_module

carrier = registry_module.ToolRegistry
guard = registry_module._require_original_registry_instance_seal
guard()

for hook in registry_module._REGISTRY_CLASS_HOOK_NAMES:
    for replacement in (None, registry_module._REGISTRY_CLASS_HOOK_ABSENT):
        type.__setattr__(carrier, hook, replacement)
        try:
            guard()
        except ValueError as exc:
            if str(exc) != "registry instance immutability contract changed":
                raise
        else:
            raise AssertionError(f"{hook} replacement was accepted")
        type.__delattr__(carrier, hook)
        guard()

"""
    completed = subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr


def test_registry_class_epoch_rejects_replaced_vectors_sentinel_and_init(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    guard = registry_module._require_original_registry_instance_seal
    guard()

    replacements = (
        (
            "_REGISTRY_CLASS_HOOK_NAMES",
            tuple(list(registry_module._REGISTRY_CLASS_HOOK_NAMES)),
        ),
        (
            "_ORIGINAL_REGISTRY_CLASS_HOOKS",
            tuple(list(registry_module._ORIGINAL_REGISTRY_CLASS_HOOKS)),
        ),
        (
            "_REGISTRY_CLASS_HOOK_ABSENT",
            object(),
        ),
        (
            "_ORIGINAL_REGISTRY_CLASS_EPOCH",
            tuple(list(registry_module._ORIGINAL_REGISTRY_CLASS_EPOCH)),
        ),
    )
    for name, replacement in replacements:
        with monkeypatch.context() as patch:
            patch.setattr(registry_module, name, replacement)
            with pytest.raises(
                ValueError,
                match="registry instance immutability contract changed",
            ):
                guard()

    registry, backend = _registry()
    original_init = vars(ToolRegistry)["__init__"]
    try:
        type.__setattr__(ToolRegistry, "__init__", None)
        with pytest.raises(
            ValueError,
            match="registry instance immutability contract changed",
        ):
            guard()
    finally:
        type.__setattr__(ToolRegistry, "__init__", original_init)

    guard()
    assert ToolRegistry._assert_registration_epoch(registry) is None
    assert backend.calls == 0


def test_static_registry_entrypoint_rejects_hostile_lookup_hook_before_state_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    registry, backend = _registry()
    invoked: list[str] = []

    def hostile_lookup(_self: object, name: str) -> object:
        invoked.append(name)
        raise AssertionError("substituted registry lookup hook must not execute")

    with monkeypatch.context() as patch:
        patch.setattr(ToolRegistry, "__getattribute__", hostile_lookup)
        with pytest.raises(
            ValueError,
            match="registry instance immutability contract changed",
        ):
            ToolRegistry._assert_registration_epoch(registry)

    assert invoked == []
    assert backend.calls == 0
