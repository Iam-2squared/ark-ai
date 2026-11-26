"""Run970: a replaced expiry-restart result guard vector fails closed.

The reviewer only processes synthetic, content-free cohort evidence.  No
Memory deletion, implicit expiry, device clock, or permission is asserted.
"""

from __future__ import annotations

import pytest

from ark.memory import expiry_restart_receipt_review as restart


@pytest.mark.parametrize("mutation", ("empty", "truncated", "reordered", "rebuilt"))
def test_rebound_result_guard_vector_rejected_before_page_access(
    monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    original = restart._FIELDS
    changed = {
        "empty": (),
        "truncated": original[:2],
        "reordered": tuple(reversed(original)),
        "rebuilt": tuple(list(original)),
    }[mutation]
    assert changed is not original

    # No caller-retained page or clock may be inspected while the verification
    # vector has been altered, even if the new tuple has equivalent values.
    with monkeypatch.context() as patch:
        patch.setattr(restart, "_FIELDS", changed)
        with pytest.raises(
            restart.MemoryExpiryRestartRejected, match="protocol changed",
        ):
            restart.review_memory_expiry_restart_receipt(
                independently_expected_scope_hashes=(),
                prior_pages=(),
                observed_pages=(),
                retained_prior=None,
                prior_asserted_now_ms=100,
                observed_asserted_now_ms=101,
            )
