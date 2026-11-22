"""Run1097: Memory expiry bridge pins the guard-vector root references.

Only inert synthetic review inputs are used. This does not authorize purge,
prove trusted time, or establish independent historical custody.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, SQLiteMemoryStore
from ark.memory import coherent_expiry_restart_bridge as bridge


@pytest.mark.parametrize(
    "mutation",
    ("empty-pair", "equal-valued-pair", "descriptor-vector"),
)
def test_rebound_root_vectors_rejected_before_input_access(
    monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    original_fields = bridge._FIELDS
    original_descriptors = bridge._ORIGINAL_FIELDS
    store = object.__new__(SQLiteMemoryStore)
    scope = MemoryScope("synthetic-owner", "private")

    with monkeypatch.context() as patch:
        if mutation == "empty-pair":
            patch.setattr(bridge, "_FIELDS", ())
            patch.setattr(bridge, "_ORIGINAL_FIELDS_VECTOR", ())
        elif mutation == "equal-valued-pair":
            clone = tuple(list(original_fields))
            assert clone == original_fields and clone is not original_fields
            patch.setattr(bridge, "_FIELDS", clone)
            patch.setattr(bridge, "_ORIGINAL_FIELDS_VECTOR", clone)
        else:
            clone = tuple(list(original_descriptors))
            assert clone == original_descriptors and clone is not original_descriptors
            patch.setattr(bridge, "_ORIGINAL_FIELDS", clone)

        with pytest.raises(
            bridge.CoherentExpiryRestartRejected, match="protocol changed",
        ):
            # _protocol must reject the altered guard roots before inspecting
            # this uninitialized store, scope tuple, or missing retained result.
            bridge.review_coherent_expiry_restart(
                store, (scope,), None, now_ms=100,
            )


def test_protocol_defaults_retain_original_guard_vector_objects() -> None:
    defaults = bridge._protocol.__defaults__
    assert type(defaults) is tuple and len(defaults) == 2
    assert defaults[0] is bridge._ORIGINAL_FIELDS_VECTOR
    assert defaults[1] is bridge._ORIGINAL_FIELDS
    bridge._protocol()
