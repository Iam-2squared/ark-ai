"""Direct Memory ID ingress must never bypass the MemoryWrite/Scope bounds."""

from __future__ import annotations

import pytest

from ark.memory.contracts import MemoryScope
from ark.memory.sqlite_store import deterministic_memory_id


class StrSubclass(str):
    pass


def test_direct_id_is_stable_and_does_not_disclose_source() -> None:
    scope = MemoryScope("owner", "private")
    result = deterministic_memory_id(scope, "secret-memory-source")
    assert result == deterministic_memory_id(scope, "secret-memory-source")
    assert len(result) == 68
    assert result.startswith("mem_")
    assert "owner" not in result and "secret" not in result


def test_direct_id_accepts_existing_bounded_unicode_contract() -> None:
    scope = MemoryScope("所有者", "個人")
    source = "記録" * 256
    assert len(source) == 512
    assert len(deterministic_memory_id(scope, source)) == 68


@pytest.mark.parametrize("source", ["x" * 513, "x" * 65536, "   "])
def test_direct_id_rejects_oversized_or_blank_source(source: str) -> None:
    with pytest.raises(ValueError):
        deterministic_memory_id(MemoryScope("owner"), source)


def test_direct_id_rejects_str_subclass_without_protocol_execution() -> None:
    with pytest.raises(TypeError):
        deterministic_memory_id(MemoryScope("owner"), StrSubclass("source"))


@pytest.mark.parametrize("source", ["bad\\ud800", "bad\\udfff"])
def test_direct_id_rejects_invalid_utf8_source(source: str) -> None:
    with pytest.raises(ValueError, match="UTF-8"):
        deterministic_memory_id(MemoryScope("owner"), source)


@pytest.mark.parametrize("field", ["owner_id", "namespace"])
def test_direct_id_rejects_mutated_oversized_scope(
    field: str,
) -> None:
    scope = MemoryScope("owner", "namespace")
    object.__setattr__(scope, field, "z" * 257)
    with pytest.raises(ValueError):
        deterministic_memory_id(scope, "source")


@pytest.mark.parametrize("field", ["owner_id", "namespace"])
def test_direct_id_rejects_mutated_string_subclass_scope(field: str) -> None:
    scope = MemoryScope("owner", "namespace")
    object.__setattr__(scope, field, StrSubclass("unexpected"))
    with pytest.raises(TypeError):
        deterministic_memory_id(scope, "source")


def test_direct_id_rejects_invalid_utf8_mutated_scope() -> None:
    scope = MemoryScope("owner", "namespace")
    object.__setattr__(scope, "owner_id", "bad\\ud800")
    with pytest.raises(ValueError, match="UTF-8"):
        deterministic_memory_id(scope, "source")


def test_direct_id_rejects_mutated_blank_scope() -> None:
    scope = MemoryScope("owner", "namespace")
    object.__setattr__(scope, "owner_id", "  ")
    with pytest.raises(ValueError):
        deterministic_memory_id(scope, "source")
