"""Disconnected atomic carrier parser drift must fail before callback access.

In-memory synthetic carriers are not independent custody or authority to act.
"""

from __future__ import annotations

import re

import pytest

from ark.agency import disconnected_atomic_input_review as review
from ark.agency.disconnected_atomic_preaction_ledger import (
    AtomicIntentClaim,
    AtomicPreactionRejected,
    genesis_atomic_preaction_witness,
)


def _carriers():
    return (
        AtomicIntentClaim("occ_" + "a" * 64, "bound_" + "b" * 64, "c" * 64),
        genesis_atomic_preaction_witness(),
    )


@pytest.mark.parametrize("surface", (
    "occurrence_pattern", "bound_pattern", "digest_pattern",
    "budget", "bool_budget", "matcher", "carrier_guard",
    "field_map", "captured_map", "hooks", "field_entry", "capture_entry",
))
def test_changed_input_protocol_denied_before_poison_callback(
    monkeypatch: pytest.MonkeyPatch, surface: str,
) -> None:
    claim, retained = _carriers()
    invoked = []

    def poison(*_args: object, **_kwargs: object) -> bool:
        invoked.append(surface)
        raise AssertionError("untrusted atomic input callback ran")

    with monkeypatch.context() as patch:
        if surface == "occurrence_pattern":
            patch.setattr(review, "_OCCURRENCE", re.compile(".*"))
        elif surface == "bound_pattern":
            patch.setattr(review, "_BOUND", re.compile(".*"))
        elif surface == "digest_pattern":
            patch.setattr(review, "_SHA", re.compile(".*"))
        elif surface == "budget":
            patch.setattr(review, "_MAX", 999)
        elif surface == "bool_budget":
            patch.setattr(review, "_MAX", True)
        elif surface == "matcher":
            patch.setattr(review, "_matches", poison)
        elif surface == "carrier_guard":
            patch.setattr(review, "_original_carriers", poison)
        elif surface == "field_map":
            patch.setattr(review, "_FIELDS", {})
        elif surface == "captured_map":
            patch.setattr(review, "_ORIGINALS", {})
        elif surface == "hooks":
            patch.setattr(review, "_HOOKS", ())
        elif surface == "field_entry":
            patch.setitem(
                review._FIELDS, AtomicIntentClaim, ("occurrence_id",),
            )
        else:
            patch.setitem(review._ORIGINALS, AtomicIntentClaim, ())

        with pytest.raises(AtomicPreactionRejected, match="protocol changed"):
            review.review_atomic_input_carriers(claim, retained)
    assert invoked == []


def test_original_atomic_input_protocol_keeps_deny_only_behavior() -> None:
    claim, retained = _carriers()
    actual = review.review_atomic_input_carriers(claim, retained)
    assert actual == (
        claim.occurrence_id, claim.bound_action_id, claim.request_sha256,
        retained.count, retained.tip_sha256,
    )
    assert type(actual) is tuple
    assert not hasattr(actual, "execute")
