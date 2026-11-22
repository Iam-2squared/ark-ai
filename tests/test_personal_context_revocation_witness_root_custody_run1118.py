"""Run1118: Personal Context revocation witness pins its vector root object.

Only synthetic witness metadata is used. No consent, disclosure or erasure
authority is created by a local continuity digest.
"""

from __future__ import annotations

import pytest

from ark import personal_context_revocation_continuity_review as continuity
from ark.personal_context_revocation_review import SyntheticContextRevocationLedger


@pytest.mark.parametrize(
    "mutation",
    ("empty-root", "equal-valued-root", "all-roots-equal-clone"),
)
def test_rebound_witness_vector_root_rejected_before_ledger_access(
    monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    original_epoch = continuity._WITNESS_VECTOR_EPOCH
    ledger = object.__new__(SyntheticContextRevocationLedger)

    with monkeypatch.context() as patch:
        if mutation == "empty-root":
            patch.setattr(continuity, "_WITNESS_VECTOR_EPOCH", ())
        elif mutation == "equal-valued-root":
            clone = tuple(list(original_epoch))
            assert clone == original_epoch and clone is not original_epoch
            patch.setattr(continuity, "_WITNESS_VECTOR_EPOCH", clone)
        else:
            fields = tuple(list(continuity._WITNESS_FIELDS))
            hooks = tuple(list(continuity._WITNESS_HOOKS))
            original_fields = tuple(list(continuity._ORIGINAL_WITNESS_FIELDS))
            original_hooks = tuple(list(continuity._ORIGINAL_WITNESS_HOOKS))
            clone_epoch = (fields, hooks, original_fields, original_hooks)
            patch.setattr(continuity, "_WITNESS_FIELDS", fields)
            patch.setattr(continuity, "_WITNESS_HOOKS", hooks)
            patch.setattr(continuity, "_ORIGINAL_WITNESS_FIELDS", original_fields)
            patch.setattr(continuity, "_ORIGINAL_WITNESS_HOOKS", original_hooks)
            patch.setattr(continuity, "_WITNESS_VECTOR_EPOCH", clone_epoch)

        with pytest.raises(
            continuity.SyntheticContextRevocationRejected,
            match="revocation digest implementation changed",
        ):
            # The first guard must reject before ledger.path is read.
            continuity.review_revocation_continuity(ledger)


def test_witness_vector_guard_retains_original_root_in_default_argument() -> None:
    defaults = continuity._require_original_witness_carrier.__defaults__
    assert type(defaults) is tuple and len(defaults) == 1
    assert defaults[0] is continuity._WITNESS_VECTOR_EPOCH
    continuity._require_original_witness_carrier()
