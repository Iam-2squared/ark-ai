"""Post-COMMIT manual Memory review refuses mutated proposals before SQLite.

All data is synthetic local Memory. No retry, tool access or external action.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.generation_fenced_cas import observe_memory_generation_for_cas
from ark.memory.postcommit_uncertainty_review import (
    MemoryCommitTriageRejected,
    review_uncertain_memory_commit,
)


@pytest.mark.parametrize(
    "mutation",
    (
        "source_multibyte", "source_surrogate", "content_oversize",
        "content_surrogate", "metadata_value_type", "metadata_surrogate",
        "metadata_multibyte", "metadata_excess", "expiry_bool",
        "expiry_negative", "scope_multibyte", "scope_surrogate",
    ),
)
def test_invalid_reflectively_changed_proposal_never_opens_private_db(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    scope = MemoryScope("owner", "private")
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    store.put(MemoryWrite(scope, "source", "before"))
    retained = observe_memory_generation_for_cas(store, scope, "source")
    proposed = MemoryWrite(scope, "source", "after")
    if mutation == "source_multibyte":
        object.__setattr__(proposed, "source_id", "あ" * 200)
    elif mutation == "source_surrogate":
        object.__setattr__(proposed, "source_id", "broken\ud800")
    elif mutation == "content_oversize":
        object.__setattr__(proposed, "content", "x" * 1_000_001)
    elif mutation == "content_surrogate":
        object.__setattr__(proposed, "content", "broken\ud800")
    elif mutation == "metadata_value_type":
        object.__setattr__(proposed, "metadata", {"key": object()})
    elif mutation == "metadata_surrogate":
        object.__setattr__(proposed, "metadata", {"key": "bad\ud800"})
    elif mutation == "metadata_multibyte":
        object.__setattr__(proposed, "metadata", {"key": "あ" * 2000})
    elif mutation == "metadata_excess":
        object.__setattr__(
            proposed, "metadata", {f"key{i}": "value" for i in range(65)},
        )
    elif mutation == "expiry_bool":
        object.__setattr__(proposed, "expires_at_ms", True)
    elif mutation == "expiry_negative":
        object.__setattr__(proposed, "expires_at_ms", -1)
    else:
        changed_scope = MemoryScope("owner", "private")
        object.__setattr__(
            changed_scope, "owner_id",
            "あ" * 100 if mutation == "scope_multibyte" else "bad\ud800",
        )
        object.__setattr__(proposed, "scope", changed_scope)

    touched: list[str] = []

    def forbidden_private_read():
        touched.append("opened")
        raise AssertionError("private Memory opened before proposal validation")

    monkeypatch.setattr(store, "_connect_readonly", forbidden_private_read)
    with pytest.raises(MemoryCommitTriageRejected):
        review_uncertain_memory_commit(store, proposed, retained_before=retained)
    assert touched == []


def test_unchanged_valid_memory_remains_manual_only(tmp_path: Path) -> None:
    scope = MemoryScope("owner", "private")
    store = SQLiteMemoryStore(tmp_path / "memory.sqlite", clock_ms=lambda: 100)
    store.put(MemoryWrite(scope, "source", "before"))
    retained = observe_memory_generation_for_cas(store, scope, "source")
    report = review_uncertain_memory_commit(
        store, MemoryWrite(scope, "source", "after"), retained_before=retained,
    )
    assert report.disposition == "LOCAL_UNCHANGED"
    assert report.automatic_retry_authorized is False
    assert report.write_authorized is False
    assert report.caller_attribution_proven is False
