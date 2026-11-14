"""Expiry cohort carries only pinned local evidence, never purge authority."""

from __future__ import annotations

import re

import pytest

import ark.memory.expiry_cohort_review as cohort
from ark.memory.expiry_candidate_preview import MemoryExpiryPreview

_SCOPE = "a" * 64


def _preview() -> MemoryExpiryPreview:
    return MemoryExpiryPreview(_SCOPE, 12, 1, False, "b" * 64, "c" * 64)


def _review() -> cohort.MemoryExpiryCohort:
    return cohort.aggregate_memory_expiry_cohort(
        independently_expected_scope_hashes=(_SCOPE,),
        previews=(_preview(),),
        asserted_now_ms=12,
    )


@pytest.mark.parametrize(
    ("name", "replacement"),
    (
        ("_SHA", re.compile(r".*\\Z")),
        ("_DOMAIN", b"unbound-domain"),
        ("_MAX_SCOPES", 65),
        ("_MAX_CANDIDATES", 64001),
        ("_MAX_TIME", (1 << 63)),
        ("_MAX_TIME", True),
        ("_PREVIEW", object),
        ("_COHORT", object),
        ("_TRANSITION", object),
        ("MemoryExpiryPreview", object),
        ("MemoryExpiryCohort", object),
        ("MemoryExpiryCohortTransition", object),
    ),
)
def test_protocol_rebind_denied_before_receipt_read(
    monkeypatch: pytest.MonkeyPatch, name: str, replacement: object,
) -> None:
    receipt = _preview()
    with monkeypatch.context() as patch:
        patch.setattr(cohort, name, replacement)
        with pytest.raises(cohort.MemoryExpiryCohortRejected, match="contract"):
            cohort.aggregate_memory_expiry_cohort(
                independently_expected_scope_hashes=(_SCOPE,),
                previews=(receipt,),
                asserted_now_ms=12,
            )
    assert _review().deletion_authorized is False


@pytest.mark.parametrize(
    ("klass", "name"),
    (
        (MemoryExpiryPreview, "__getattribute__"),
        (MemoryExpiryPreview, "__getattr__"),
        (cohort.MemoryExpiryCohort, "__getattribute__"),
        (cohort.MemoryExpiryCohortTransition, "__getattribute__"),
    ),
)
def test_rebound_carrier_hooks_are_rejected(
    monkeypatch: pytest.MonkeyPatch, klass: type, name: str,
) -> None:
    with monkeypatch.context() as patch:
        patch.setattr(klass, name, lambda *_: None, raising=False)
        with pytest.raises(cohort.MemoryExpiryCohortRejected, match="contract"):
            _review()


def test_substituted_private_receipt_field_does_not_execute_getter(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    receipt = _preview()

    def leak(_: object) -> object:
        raise AssertionError("private receipt getter must not run")

    with monkeypatch.context() as patch:
        patch.setattr(MemoryExpiryPreview, "scope_sha256", property(leak))
        with pytest.raises(cohort.MemoryExpiryCohortRejected, match="contract"):
            cohort.aggregate_memory_expiry_cohort(
                independently_expected_scope_hashes=(_SCOPE,),
                previews=(receipt,),
                asserted_now_ms=12,
            )


def test_comparison_denied_before_reading_rebound_cohort_field(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first = _review()
    with monkeypatch.context() as patch:
        patch.setattr(cohort.MemoryExpiryCohort, "cohort_sha256", property(
            lambda _: (_ for _ in ()).throw(AssertionError("private digest read")),
        ))
        with pytest.raises(cohort.MemoryExpiryCohortRejected, match="contract"):
            cohort.compare_memory_expiry_cohorts(first, first)
