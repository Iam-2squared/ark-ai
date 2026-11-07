"""Two passive Memory COMMIT reviewers expose auditable local receipt inputs.

The digest proves only consistency of the local diagnostic payload; it does
not prove writer identity, a COMMIT by the caller, or permission to retry.
"""

from __future__ import annotations

import hashlib
import json

import pytest
from test_memory_postcommit_triage_run552 import make_case

from ark import memory
from ark.memory import ambiguous_commit_pair_review as mod
from ark.memory.generation_fenced_cas import generation_fenced_memory_update


@pytest.mark.parametrize(
    ("change", "expected"),
    (
        ("unchanged", "LOCAL_UNCHANGED_REVIEW"),
        ("matching", "MATCHING_ROW_MANUAL_REVIEW"),
        ("diverged", "DIVERGED_MANUAL_REVIEW"),
    ),
)
def test_dual_observer_receipts_are_publicly_reconstructible_but_not_authority(
    tmp_path, change, expected,
):
    store, scope, _, retained, proposed = make_case(tmp_path)
    if change == "matching":
        generation_fenced_memory_update(store, proposed, retained=retained)
    elif change == "diverged":
        generation_fenced_memory_update(
            store,
            memory.MemoryWrite(
                scope, "stable", "other", metadata={"source": "local"},
            ),
            retained=retained,
        )

    result = mod.review_memory_ambiguous_commit_pair(
        store, proposed, retained=retained,
    )
    fields = (
        result.disposition,
        result.retained_prefix_sha256,
        result.observed_prefix_sha256,
        result.observed_row_sha256,
        result.triage_receipt_sha256,
        result.outcome_receipt_sha256,
    )
    assert result.disposition == expected
    assert all(
        type(value) is str and len(value) == 64
        for value in fields[1:]
    )
    calculated = hashlib.sha256(
        mod._DOMAIN + json.dumps(
            fields, ensure_ascii=True, separators=(",", ":"),
        ).encode("ascii")
    ).hexdigest()
    assert calculated == result.reconciliation_sha256
    assert result.reconciliation_sha256 == (
        mod.review_memory_ambiguous_commit_pair(
            store, proposed, retained=retained,
        ).reconciliation_sha256
    )
    assert all(getattr(result, name) is False for name in mod._DENIALS)
    assert "other" not in repr(result) and "private" not in repr(result)
