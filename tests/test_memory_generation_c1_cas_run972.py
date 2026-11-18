"""Run972: opt-in generation CAS rejects C1 identity aliases before SQLite.

The frozen Memory v1 scope contract continues to permit opaque labels. No
consent, trusted clock, hardware, or real action authority is conferred.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_fenced_cas as cas

_C1 = ("\u0080", "\u0081", "\u0085", "\u008d", "\u009b", "\u009f")


@pytest.mark.parametrize("control", _C1)
@pytest.mark.parametrize("field", ("owner_id", "namespace", "source_id"))
def test_c1_identity_denied_before_observation_or_update_database_access(
    control: str, field: str,
) -> None:
    # No path or connection was ever initialized: reaching SQLite raises an
    # unrelated error instead of the specific identity-admission refusal.
    store = object.__new__(SQLiteMemoryStore)
    scope = MemoryScope("synthetic-owner", "private")
    source = "synthetic-source"
    if field == "source_id":
        source = "synthetic" + control + "-source"
    else:
        object.__setattr__(
            scope, field, getattr(scope, field) + control + "spoof",
        )
    with pytest.raises(cas.MemoryGenerationCASRejected, match="formatting control"):
        cas.observe_memory_generation_for_cas(store, scope, source)
    # This malformed identity is accepted by the frozen generic MemoryWrite
    # constructor but must be rejected at the stricter opt-in CAS boundary.
    write = MemoryWrite(scope, source, "no local update")
    with pytest.raises(cas.MemoryGenerationCASRejected, match="formatting control"):
        cas.generation_fenced_memory_update(
            store, write, retained=object.__new__(cas.MemoryGenerationCASToken),
        )


def test_normal_japanese_identifiers_remain_valid_in_opt_in_cas() -> None:
    scope = MemoryScope("端末所有者", "個人")
    cas._require_bounded_scope(scope)
    cas._require_bounded_source_id("記録-東京")
    # Frozen v1 remains unchanged; optional admission is deliberately stricter.
    assert MemoryScope("端末所有者\u009b", "個人").owner_id.endswith("\u009b")
