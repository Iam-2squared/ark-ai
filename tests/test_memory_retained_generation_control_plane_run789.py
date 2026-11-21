"""Retained Memory verification cannot silently drop denial/field checks.

No cross-process witness authentication or Memory mutation is provided.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import retained_generation_fence as fence
from ark.memory.cas_generation_review import review_memory_revision_reuse


def _fixture(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "retained-control-plane.sqlite",
        clock_ms=lambda: 1000,
    )
    scope = MemoryScope("fixture-owner", "notes")
    store.put(MemoryWrite(scope, "fixture-source", "private synthetic value"))
    retained = review_memory_revision_reuse(
        store, scope, "fixture-source", expected_revision=1,
    )
    return store, scope, retained


@pytest.mark.parametrize("surface", (
    "denial_names", "field_names", "hook_names", "review_type",
    "denial_descriptors", "field_descriptors", "hook_descriptors",
    "original_review_callback",
))
def test_replaced_verification_baseline_rejected_before_private_sqlite(
    tmp_path, monkeypatch: pytest.MonkeyPatch, surface: str,
) -> None:
    store, scope, retained = _fixture(tmp_path)
    with monkeypatch.context() as patch:
        if surface == "denial_names":
            patch.setattr(fence, "_DENIALS", ())
        elif surface == "field_names":
            patch.setattr(fence, "_FIELDS", ())
        elif surface == "hook_names":
            patch.setattr(fence, "_HOOKS", ())
        elif surface == "review_type":
            patch.setattr(fence, "_REVIEW_TYPE", object)
        elif surface == "denial_descriptors":
            patch.setattr(fence, "_ORIGINAL_DENIALS", ())
        elif surface == "field_descriptors":
            patch.setattr(fence, "_ORIGINAL_FIELDS", ())
        elif surface == "hook_descriptors":
            patch.setattr(fence, "_ORIGINAL_HOOKS", ())
        else:
            patch.setattr(fence, "_ORIGINAL_REVIEW", object())

        with pytest.raises(
            fence.RetainedMemoryGenerationRejected,
            match="parser or review helper changed",
        ):
            fence.verify_retained_memory_generation(
                retained, store, scope, "fixture-source", expected_revision=1,
            )
    assert retained.write_authorized is False
    assert retained.generation_authenticated is False


def test_original_retained_memory_baselines_are_read_only(tmp_path) -> None:
    store, scope, retained = _fixture(tmp_path)
    assert fence.verify_retained_memory_generation(
        retained, store, scope, "fixture-source", expected_revision=1,
    ) is None
    assert retained.write_authorized is False
    assert retained.erase_authorized is False
