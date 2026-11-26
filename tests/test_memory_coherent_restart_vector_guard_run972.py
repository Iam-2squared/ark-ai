"""Run972: expiry restart bridge guards its own field-vector definition.

Only synthetic, read-only Memory review is involved: no automatic purge,
trusted time, disclosure authorization, or real action is inferred.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, SQLiteMemoryStore
from ark.memory import coherent_expiry_restart_bridge as bridge


@pytest.mark.parametrize("variant", ("empty", "short", "reversed", "rebuilt"))
def test_rebound_result_vector_rejected_before_store_or_scope_access(
    monkeypatch: pytest.MonkeyPatch, variant: str,
) -> None:
    original = bridge._FIELDS
    mutated = {
        "empty": (),
        "short": original[:-1],
        "reversed": tuple(reversed(original)),
        "rebuilt": tuple(list(original)),
    }[variant]
    assert mutated is not original
    # The exact SQLite store is uninitialized. Reaching either storage or a
    # caller-retained snapshot before checking the guard is a test failure.
    store = object.__new__(SQLiteMemoryStore)
    scope = MemoryScope("synthetic-owner", "private")
    with monkeypatch.context() as patch:
        patch.setattr(bridge, "_FIELDS", mutated)
        with pytest.raises(
            bridge.CoherentExpiryRestartRejected, match="protocol changed",
        ):
            bridge.review_coherent_expiry_restart(
                store, (scope,), None, now_ms=100,
            )


def test_unmodified_expiry_bridge_field_protocol_remains_pinned() -> None:
    assert bridge._FIELDS is bridge._ORIGINAL_FIELDS_VECTOR
    bridge._protocol()
