"""Fail-closed, preaccess custody of the coherent Memory WAL digest codec.

All rows are disposable SQLite fixture rows. These tests do not establish
historical writer provenance, independent retention, disclosure, or execution.
"""

from __future__ import annotations

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory.sqlite_event_alignment import review_memory_event_alignment
from ark.memory.sqlite_event_prefix_review import capture_local_memory_event_prefix
from ark.memory import sqlite_retained_coherent_review as coherent


def _fixture(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "coherent-codec.sqlite", clock_ms=lambda: 1_000,
    )
    store.put(MemoryWrite(MemoryScope("owner-a", "private"), "one", "local"))
    return (
        store,
        capture_local_memory_event_prefix(store),
        review_memory_event_alignment(store),
    )


@pytest.mark.parametrize("mutation", (
    "hashlib_module", "json_module", "different_domain", "mutable_domain",
))
def test_coherent_digest_codec_change_refused_before_sqlite_open(
    tmp_path, monkeypatch: pytest.MonkeyPatch, mutation: str,
) -> None:
    store, retained_prefix, retained_alignment = _fixture(tmp_path)
    def forbidden_open():
        raise AssertionError("tampered codec reached private SQLite")
    with monkeypatch.context() as patch:
        patch.setattr(store, "_connect_readonly", forbidden_open)
        if mutation == "hashlib_module":
            patch.setattr(coherent, "hashlib", object())
        elif mutation == "json_module":
            patch.setattr(coherent, "json", object())
        elif mutation == "different_domain":
            patch.setattr(coherent, "_RESULT_DOMAIN", b"untrusted-domain")
        else:
            patch.setattr(
                coherent, "_RESULT_DOMAIN",
                bytearray(coherent._RESULT_DOMAIN),
            )
        with pytest.raises(
            coherent.MemoryCoherentHistoryRejected,
            match="digest implementation or domain changed",
        ):
            coherent.review_retained_coherent_memory(
                store, retained_prefix, retained_alignment,
            )


@pytest.mark.parametrize("boundary", ("record", "alignment_hash", "event_hash"))
def test_coherent_digest_codec_drift_during_wal_snapshot_refused(
    tmp_path, monkeypatch: pytest.MonkeyPatch, boundary: str,
) -> None:
    store, retained_prefix, retained_alignment = _fixture(tmp_path)
    with monkeypatch.context() as patch:
        if boundary == "record":
            original = coherent._record

            def altered(row):
                decoded = original(row)
                patch.setattr(coherent, "_RESULT_DOMAIN", b"changed-after-row")
                return decoded

            patch.setattr(coherent, "_record", altered)
        elif boundary == "alignment_hash":
            original = coherent.alignment._charge

            def altered(*args, **kwargs):
                result = original(*args, **kwargs)
                patch.setattr(coherent, "json", object())
                return result

            patch.setattr(coherent.alignment, "_charge", altered)
        else:
            original = coherent.prefix._charge

            def altered(*args, **kwargs):
                result = original(*args, **kwargs)
                patch.setattr(coherent, "hashlib", object())
                return result

            patch.setattr(coherent.prefix, "_charge", altered)
        with pytest.raises(
            coherent.MemoryCoherentHistoryRejected,
            match="digest implementation or domain changed",
        ):
            coherent.review_retained_coherent_memory(
                store, retained_prefix, retained_alignment,
            )


def test_normal_coherent_memory_review_remains_read_only_and_denial_only(
    tmp_path,
) -> None:
    store, retained_prefix, retained_alignment = _fixture(tmp_path)
    store.put(MemoryWrite(MemoryScope("owner-b", "tasks"), "two", "other"))
    result = coherent.review_retained_coherent_memory(
        store, retained_prefix, retained_alignment,
    )
    assert result.previous_event_count == 1
    assert result.current_event_count == 2
    assert result.status == "ADVANCED_PREFIX_UNAUTHENTICATED"
    assert result.independently_authenticated is False
    assert result.consent_verified is False
    assert result.memory_disclosure_authorized is False
    assert result.action_authorized is False
    assert result.cross_store_atomicity_proven is False
