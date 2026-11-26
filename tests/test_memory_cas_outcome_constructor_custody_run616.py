"""Fail-closed CAS outcome report construction, without external writes.

An original False-only report property is not sufficient when __init__ can
be replaced with an executable callback. Local SQLite fixtures only.
"""

from __future__ import annotations

import pytest
from test_memory_generation_cas_outcome_run536 import _case

from ark.memory import generation_cas_outcome_review as outcome


@pytest.mark.parametrize("stage", ("preinstalled", "hash_callback"))
def test_replaced_actual_result_constructor_never_runs(tmp_path, monkeypatch, stage):
    store, _, _, retained, proposed = _case(tmp_path)
    constructor_calls = []
    opened = []
    hash_calls = []
    original_hash = outcome.hashlib.sha256

    def malicious_init(self, *args):
        constructor_calls.append(args)

    if stage == "preinstalled":
        def forbidden_read(self):
            opened.append(True)
            raise AssertionError("must preflight constructor before SQLite")

        monkeypatch.setattr(type(store), "_connect_readonly", forbidden_read)
        monkeypatch.setattr(
            outcome.MemoryCASOutcomeReview, "__init__", malicious_init,
        )
    else:
        def replace_during_hash(payload):
            hash_calls.append(True)
            monkeypatch.setattr(
                outcome.MemoryCASOutcomeReview, "__init__", malicious_init,
            )
            return original_hash(payload)

        monkeypatch.setattr(outcome.hashlib, "sha256", replace_during_hash)

    with pytest.raises(
        outcome.MemoryCASOutcomeRejected,
        match=(
            "digest implementation changed" if stage == "hash_callback"
            else "authority definition changed|manual inspection required"
        ),
    ):
        outcome.review_memory_generation_cas_outcome(
            store, proposed, retained=retained,
        )
    assert constructor_calls == []
    assert opened == []
    assert hash_calls == []  # Poisoned SHA hook is now refused at preflight.


def test_unmodified_report_keeps_manual_only_disposition(tmp_path):
    store, _, _, retained, proposed = _case(tmp_path)
    report = outcome.review_memory_generation_cas_outcome(
        store, proposed, retained=retained,
    )
    assert type(report) is outcome.MemoryCASOutcomeReview
    assert report.observation == "UNCHANGED_OBSERVED"
    assert report.commit_attributed_to_caller is False
    assert report.automatic_retry_authorized is False
    assert report.external_action_authorized is False
