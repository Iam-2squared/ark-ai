"""Startup fixture class/descriptor custody must never run substituted equality.

This is an in-process, deny-only test, not readiness or notification authority.
"""

from __future__ import annotations

import pytest

from ark import proactive_startup_fence_review as fence


def test_unchanged_startup_protocol_is_inert() -> None:
    assert fence._require_original_authorities() is None


def test_substituted_source_class_rejected_without_metaclass_equality(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    invoked: list[str] = []

    class PoisonedType(type):
        def __eq__(cls, other: object) -> bool:
            invoked.append("eq")
            raise AssertionError("class equality executed")

        def __ne__(cls, other: object) -> bool:
            invoked.append("ne")
            raise AssertionError("class inequality executed")

    class PoisonedComponent(metaclass=PoisonedType):
        pass

    monkeypatch.setattr(fence, "ComponentResult", PoisonedComponent)
    with pytest.raises(
        fence.SyntheticProactiveStartupRejected,
        match="authority descriptor epoch changed",
    ):
        fence._require_original_authorities()
    assert invoked == []


@pytest.mark.parametrize("position", (0, 1, 2, 3, 4, 5))
def test_substituted_source_descriptor_never_compares(
    monkeypatch: pytest.MonkeyPatch, position: int,
) -> None:
    invoked: list[str] = []

    class PoisonedDescriptor:
        def __eq__(self, other: object) -> bool:
            invoked.append("eq")
            raise AssertionError("descriptor equality executed")

        def __ne__(self, other: object) -> bool:
            invoked.append("ne")
            raise AssertionError("descriptor inequality executed")

        def __get__(self, instance: object, owner: type | None = None) -> object:
            invoked.append("get")
            raise AssertionError("descriptor getter executed")

    carrier = fence._SOURCE_TYPES[position]
    field = fence._SOURCE_FIELDS[position][0]
    monkeypatch.setattr(carrier, field, PoisonedDescriptor())
    with pytest.raises(
        fence.SyntheticProactiveStartupRejected,
        match="authority descriptor epoch changed",
    ):
        fence._require_original_authorities()
    assert invoked == []
