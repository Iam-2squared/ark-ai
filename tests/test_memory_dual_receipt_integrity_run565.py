"""Memory dual-review receipt integrity: both read-only digests matter."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace

import pytest
from test_memory_postcommit_triage_run552 import make_case

from ark.memory import ambiguous_commit_pair_review as mod


def _review(store, proposed, retained):
    return mod.review_memory_ambiguous_commit_pair(
        store, proposed, retained=retained,
    )


def _replace_outcome(monkeypatch, replacement):
    monkeypatch.setattr(mod, "_OUTCOME_FN", replacement)
    monkeypatch.setattr(
        mod.outcome_module, "review_memory_generation_cas_outcome",
        replacement,
    )


def test_outcome_receipt_drift_between_read_only_passes_fails_closed(
    monkeypatch, tmp_path,
):
    store, _, _, retained, proposed = make_case(tmp_path)
    original = mod._OUTCOME_FN
    calls = 0

    def drifting(*args, **kwargs):
        nonlocal calls
        calls += 1
        result = original(*args, **kwargs)
        return replace(
            result, review_sha256=("f" * 64 if calls == 2 else result.review_sha256),
        )

    _replace_outcome(monkeypatch, drifting)
    with pytest.raises(mod.MemoryAmbiguityPairRejected, match="child digest mismatch"):
        _review(store, proposed, retained)
    assert calls == 2


@pytest.mark.parametrize("invalid", ("not-a-hash", "", "G" * 64))
def test_malformed_second_reviewer_receipt_is_not_evidence(
    monkeypatch, tmp_path, invalid,
):
    store, _, _, retained, proposed = make_case(tmp_path)
    original = mod._OUTCOME_FN

    def invalid_receipt(*args, **kwargs):
        return replace(original(*args, **kwargs), review_sha256=invalid)

    _replace_outcome(monkeypatch, invalid_receipt)
    with pytest.raises(mod.MemoryAmbiguityPairRejected, match="digest"):
        _review(store, proposed, retained)


def test_manual_reconciliation_hash_binds_both_read_only_receipts(tmp_path):
    store, _, _, retained, proposed = make_case(tmp_path)
    triage = mod._TRIAGE_FN(store, proposed, retained_before=retained)
    outcome = mod._OUTCOME_FN(store, proposed, retained=retained)
    actual = _review(store, proposed, retained)
    payload = (
        actual.disposition, actual.retained_prefix_sha256,
        actual.observed_prefix_sha256, actual.observed_row_sha256,
        triage.report_sha256, outcome.review_sha256,
    )
    expected = hashlib.sha256(
        mod._DOMAIN
        + json.dumps(payload, separators=(",", ":"), ensure_ascii=True)
        .encode("ascii")
    ).hexdigest()
    assert actual.reconciliation_sha256 == expected
    assert actual.automatic_retry_authorized is False
    assert actual.write_authorized is False
