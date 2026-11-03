"""Manual Memory ambiguity review must pin retained token field carriers.

Local read-only reviewers and temporary SQLite only. This diagnostic cannot
authenticate a caller, attribute a COMMIT, grant consent or permit a retry.
"""

from __future__ import annotations

import pytest
from test_memory_postcommit_triage_run552 import make_case

from ark.memory import ambiguous_commit_pair_review as mod


@pytest.mark.parametrize("field", ("event_prefix_sha256", "row_sha256"))
def test_equal_digest_carrier_swap_during_first_review_is_rejected(
    tmp_path, monkeypatch, field,
):
    store, _, _, retained, proposed = make_case(tmp_path)
    original = mod._TRIAGE_FN

    def swapped(*args, **kwargs):
        result = original(*args, **kwargs)
        old = getattr(retained, field)
        replacement = old.encode("ascii").decode("ascii")
        assert replacement == old and replacement is not old
        object.__setattr__(retained, field, replacement)
        return result

    monkeypatch.setattr(mod, "_TRIAGE_FN", swapped)
    monkeypatch.setattr(mod.triage_module, "review_uncertain_memory_commit", swapped)
    with pytest.raises(
        mod.MemoryAmbiguityPairRejected, match="input epoch changed",
    ):
        mod.review_memory_ambiguous_commit_pair(
            store, proposed, retained=retained,
        )
    # No Memory write or retry is part of reconciliation.
    assert store.get(retained.memory_id, proposed.scope).revision == 1
    assert len(store.events(proposed.scope)) == 1


def test_unchanged_token_still_returns_denial_only_receipt(tmp_path):
    store, _, _, retained, proposed = make_case(tmp_path)
    review = mod.review_memory_ambiguous_commit_pair(
        store, proposed, retained=retained,
    )
    assert review.disposition == "LOCAL_UNCHANGED_REVIEW"
    assert review.automatic_retry_authorized is False
    assert review.caller_commit_authenticated is False
    assert review.write_authorized is False
