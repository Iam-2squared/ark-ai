"""Run750: Memory CAS outcome cannot skip its cross-scope event high-water audit.

All state is disposable and local. A CAS observation never attributes a
commit, grants consent or authorizes retry or external execution.
"""

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import generation_cas_outcome_review as outcome
from ark.memory import generation_fenced_cas as cas
from ark.memory.generation_fenced_cas import MemoryGenerationCASToken


@pytest.mark.parametrize("replacement", ("noop", "poisoned", "none"))
def test_substituted_global_history_validator_rejected_before_sqlite(
    monkeypatch, replacement,
):
    # A syntactically valid pre-access carrier; its uninitialized store must
    # NEVER be inspected after a required audit implementation is replaced.
    store = object.__new__(SQLiteMemoryStore)
    scope = MemoryScope("synthetic-owner", "private")
    proposed = MemoryWrite(scope, "synthetic-source", "private test content")
    token = MemoryGenerationCASToken(
        "mem_" + "a" * 64, 1, 1, 1, "b" * 64, "c" * 64,
    )
    calls = []

    def noop(_connection):
        calls.append("skipped global integrity")
        return None

    def poisoned(_connection):
        calls.append("executed unsafe global check")
        raise AssertionError("substituted high-water validator executed")

    candidate = {
        "noop": noop,
        "poisoned": poisoned,
        "none": None,
    }[replacement]
    with monkeypatch.context() as patch:
        patch.setattr(outcome, "_check_global_memory_event_highwater", candidate)
        with pytest.raises(
            outcome.MemoryCASOutcomeRejected,
            match="CAS global history validator changed",
        ):
            outcome.review_memory_generation_cas_outcome(
                store, proposed, retained=token,
            )
    assert calls == []


def test_original_global_history_check_preserves_manual_only_review(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "cas-audit.sqlite3", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("synthetic-owner", "private")
    store.put(MemoryWrite(scope, "fixture", "initial"), expected_revision=0)
    retained = cas.observe_memory_generation_for_cas(store, scope, "fixture")
    proposed = MemoryWrite(scope, "fixture", "next")
    result = outcome.review_memory_generation_cas_outcome(
        store, proposed, retained=retained,
    )
    assert result.observation == "UNCHANGED_OBSERVED"
    assert result.automatic_retry_authorized is False
    assert result.commit_attributed_to_caller is False
    assert result.external_action_authorized is False
