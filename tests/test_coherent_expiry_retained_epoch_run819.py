"""Retained Memory evidence must not drift inside a later SQLite callback."""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import coherent_expiry_restart_bridge as restart
from ark.memory.coherent_expiry_snapshot_review import review_coherent_expiry_snapshot


def _case(tmp_path):
    store = SQLiteMemoryStore(tmp_path / "expiry-epoch.sqlite", clock_ms=lambda: 1000)
    scopes = (MemoryScope("owner", "notes"), MemoryScope("owner", "tasks"))
    store.put(MemoryWrite(scopes[0], "a", "private-a", expires_at_ms=1200))
    store.put(MemoryWrite(scopes[1], "b", "private-b", expires_at_ms=1400))
    prior = review_coherent_expiry_snapshot(store, scopes, now_ms=1500)
    return store, scopes, prior


def test_quiescent_retained_pages_are_still_readonly(tmp_path):
    store, scopes, prior = _case(tmp_path)
    reviewed = restart.review_coherent_expiry_restart(
        store, scopes, prior, now_ms=1500,
    )
    assert reviewed.transition == "UNCHANGED_LOCAL_CLAIM"
    assert reviewed.previous_candidates == 2
    assert reviewed.observed_candidates == 2
    assert reviewed.automatic_purge_authorized is False
    assert reviewed.cross_epoch_atomicity_proven is False
    assert "private" not in repr(reviewed)


@pytest.mark.parametrize(
    "field",
    (
        "page-count", "page-digest", "page-more",
        "cohort-count", "cohort-digest", "cohort-time",
        "cohort-truncated", "cohort-inventory",
    ),
)
def test_reentrant_retained_page_or_cohort_mutation_refused_before_transition(
    tmp_path, monkeypatch, field,
):
    store, scopes, prior = _case(tmp_path)
    original_open = store._connect_readonly
    calls = []

    def mutate_on_open():
        calls.append(field)
        if field == "page-count":
            object.__setattr__(
                prior.pages[0], "candidate_count", prior.pages[0].candidate_count + 1,
            )
        elif field == "page-digest":
            object.__setattr__(prior.pages[0], "preview_sha256", "f" * 64)
        elif field == "page-more":
            object.__setattr__(prior.pages[0], "has_more", True)
        elif field == "cohort-count":
            object.__setattr__(
                prior.cohort, "candidate_count", prior.cohort.candidate_count + 1,
            )
        elif field == "cohort-digest":
            object.__setattr__(prior.cohort, "cohort_sha256", "f" * 64)
        elif field == "cohort-time":
            object.__setattr__(prior.cohort, "asserted_now_ms", 1501)
        elif field == "cohort-truncated":
            object.__setattr__(
                prior.cohort, "truncated_scopes", (prior.pages[0].scope_sha256,),
            )
        else:
            object.__setattr__(
                prior.cohort, "scope_hashes", (prior.pages[0].scope_sha256,),
            )
        return original_open()

    monkeypatch.setattr(store, "_connect_readonly", mutate_on_open)
    with pytest.raises(
        restart.CoherentExpiryRestartRejected, match="inputs changed",
    ):
        restart.review_coherent_expiry_restart(store, scopes, prior, now_ms=1500)
    assert calls == [field]
