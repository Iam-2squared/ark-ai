"""Read-only Memory lifetime/ABA review refuses hostile labels before I/O."""

from __future__ import annotations

from dataclasses import replace

import pytest

from ark.memory import MemoryScope, SQLiteMemoryStore
from ark.memory import cas_generation_review as review


@pytest.mark.parametrize(
    "case",
    (
        "source-surrogate", "source-overbudget", "source-subclass",
        "owner-surrogate", "owner-overbudget", "owner-subclass",
        "namespace-surrogate", "namespace-overbudget",
    ),
)
def test_reject_reflected_utf8_identity_before_memory_store_path_access(case):
    # No path exists on this exact-type handle. If the boundary tries to
    # connect or hash a malformed identity before rejection, this test fails.
    store = object.__new__(SQLiteMemoryStore)
    scope = MemoryScope("fixture-owner", "private")
    source = "test-source"
    called = []

    class HostileStr(str):
        def __hash__(self):
            called.append("hash")
            raise AssertionError("untrusted source hash executed")

        def __eq__(self, other):
            called.append("eq")
            raise AssertionError("untrusted source equality executed")

    invalid = {
        "surrogate": "bad\ud800",
        "overbudget": "界" * 200,
        "subclass": HostileStr("fixture-owner"),
    }
    target, kind = case.split("-", 1)
    if target == "source":
        source = invalid[kind]
    else:
        scope = replace(scope)
        object.__setattr__(scope, target + "_id" if target == "owner" else target,
                           invalid[kind])
    with pytest.raises(
        review.MemoryGenerationReviewRejected, match="exact bounded",
    ):
        review.review_memory_revision_reuse(
            store, scope, source, expected_revision=0,
        )
    assert called == []


def test_readonly_generation_utf8_byte_boundaries():
    assert review._strict_utf8_identity("界" * 85, 256)
    assert not review._strict_utf8_identity("界" * 86, 256)
    assert review._strict_utf8_identity("界" * 170, 512)
    assert not review._strict_utf8_identity("界" * 171, 512)


def test_replaced_generation_utf8_validator_rejected_before_private_access(
    monkeypatch,
):
    store = object.__new__(SQLiteMemoryStore)
    scope = MemoryScope("fixture-owner", "private")
    touched = []
    with monkeypatch.context() as patch:
        patch.setattr(
            review, "_strict_utf8_identity",
            lambda *args: touched.append(args),
        )
        with pytest.raises(
            review.MemoryGenerationReviewRejected, match="constructor",
        ):
            review.review_memory_revision_reuse(
                store, scope, "test-source", expected_revision=0,
            )
    assert touched == []
