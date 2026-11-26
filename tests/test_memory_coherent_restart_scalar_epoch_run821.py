"""Memory restart receipt must reject Python-equal but differently typed epochs."""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import coherent_expiry_restart_bridge as bridge
from ark.memory.coherent_expiry_snapshot_review import review_coherent_expiry_snapshot


@pytest.mark.parametrize(
    ("target", "replacement"),
    (
        ("page_count", True),
        ("page_more", 0),
        ("page_clock", 1500.0),
        ("cohort_count", 2.0),
        ("cohort_clock", 1500.0),
    ),
)
def test_reentrant_equal_numeric_substitution_rejected_before_second_read(
    tmp_path, monkeypatch: pytest.MonkeyPatch, target: str, replacement: object,
) -> None:
    store = SQLiteMemoryStore(
        tmp_path / "coherent-scalar-epoch.sqlite", clock_ms=lambda: 1000,
    )
    scopes = (MemoryScope("owner", "alpha"), MemoryScope("owner", "beta"))
    store.put(MemoryWrite(scopes[0], "first", "private-one", expires_at_ms=1200))
    store.put(MemoryWrite(scopes[1], "second", "private-two", expires_at_ms=1200))
    prior = review_coherent_expiry_snapshot(store, scopes, now_ms=1500)
    assert prior.pages[0].candidate_count == 1
    assert prior.cohort.candidate_count == 2
    assert prior.pages[0].has_more is False

    original_open = store._connect_readonly
    openings = []

    def interleaved_open():
        openings.append(target)
        if target.startswith("page"):
            field = {
                "page_count": "candidate_count",
                "page_more": "has_more",
                "page_clock": "read_at_ms",
            }[target]
            original = getattr(prior.pages[0], field)
            assert original == replacement and type(original) is not type(replacement)
            object.__setattr__(prior.pages[0], field, replacement)
        else:
            field = {
                "cohort_count": "candidate_count",
                "cohort_clock": "asserted_now_ms",
            }[target]
            original = getattr(prior.cohort, field)
            assert original == replacement and type(original) is not type(replacement)
            object.__setattr__(prior.cohort, field, replacement)
        return original_open()

    monkeypatch.setattr(store, "_connect_readonly", interleaved_open)
    with pytest.raises(
        bridge.CoherentExpiryRestartRejected, match="inputs changed",
    ):
        bridge.review_coherent_expiry_restart(
            store, scopes, prior, now_ms=1500,
        )
    assert openings == [target]


@pytest.mark.parametrize("target", ("page_hash", "cohort_scopes"))
def test_same_value_receipt_carrier_replacement_rejected(
    tmp_path, monkeypatch: pytest.MonkeyPatch, target: str,
) -> None:
    store = SQLiteMemoryStore(
        tmp_path / "coherent-same-value.sqlite", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("owner", "notes")
    store.put(MemoryWrite(scope, "id", "private", expires_at_ms=1200))
    prior = review_coherent_expiry_snapshot(store, (scope,), now_ms=1500)
    original_open = store._connect_readonly
    openings = []

    def interleaved_open():
        openings.append(target)
        if target == "page_hash":
            old = prior.pages[0].scope_sha256
            new = ("_" + old)[1:]
            assert new == old and new is not old
            object.__setattr__(prior.pages[0], "scope_sha256", new)
        else:
            old = prior.cohort.scope_hashes
            new = tuple(list(old))
            assert new == old and new is not old
            object.__setattr__(prior.cohort, "scope_hashes", new)
        return original_open()

    monkeypatch.setattr(store, "_connect_readonly", interleaved_open)
    with pytest.raises(
        bridge.CoherentExpiryRestartRejected, match="inputs changed",
    ):
        bridge.review_coherent_expiry_restart(
            store, (scope,), prior, now_ms=1500,
        )
    assert openings == [target]
