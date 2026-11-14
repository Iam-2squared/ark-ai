"""Private Memory row-delta metadata must never reach swapped digest codecs.

A retained row commitment is a local consistency witness, not independent
writer attribution, privacy consent or an authorization to disclose.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import sqlite_retained_row_delta_review as delta


def _fixture(tmp_path):
    source = SQLiteMemoryStore(
        tmp_path / "private-rows.sqlite3", clock_ms=lambda: 1000,
    )
    source.put(
        MemoryWrite(MemoryScope("owner", "private"), "note", "private fixture"),
        expected_revision=0,
    )
    return source, delta.capture_local_memory_row_delta(source)


@pytest.mark.parametrize("operation", ("capture", "review"))
@pytest.mark.parametrize("dependency", ("hashlib", "json", "_DOMAIN", "_REVIEW_DOMAIN"))
def test_changed_digest_contract_rejected_before_private_memory_scan(
    tmp_path, monkeypatch: pytest.MonkeyPatch, operation: str,
    dependency: str,
) -> None:
    source, retained = _fixture(tmp_path)
    invoked: list[str] = []

    def poison(*_args: object, **_kwargs: object) -> object:
        invoked.append(dependency)
        raise AssertionError("private Memory input reached substituted codec")

    if dependency == "hashlib":
        replacement = SimpleNamespace(sha256=poison)
    elif dependency == "json":
        replacement = SimpleNamespace(dumps=poison)
    else:
        replacement = b"untrusted-domain"

    with monkeypatch.context() as patch:
        patch.setattr(delta, dependency, replacement)

        def unexpected_scan(_source):
            raise AssertionError("Memory store scanned before digest veto")

        patch.setattr(delta, "_scan", unexpected_scan)
        with pytest.raises(
            delta.MemoryRowDeltaRejected,
            match="digest dependencies changed",
        ):
            if operation == "capture":
                delta.capture_local_memory_row_delta(source)
            else:
                delta.review_retained_memory_row_delta(source, retained)
    assert invoked == []
    assert delta.capture_local_memory_row_delta(source) == retained


def test_original_memory_row_digest_remains_no_authority(tmp_path) -> None:
    source, retained = _fixture(tmp_path)
    review = delta.review_retained_memory_row_delta(source, retained)
    assert review.appended_events == 0
    assert review.explained_changes == 0
    assert review.writer_authenticated is False
    assert review.disclosure_authorized is False
    assert review.action_authorized is False
    assert retained.independently_authenticated is False
    assert retained.action_authorized is False
