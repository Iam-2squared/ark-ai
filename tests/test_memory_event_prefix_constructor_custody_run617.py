"""Original Memory event-prefix constructors must not execute injected code.

All evidence is local and caller-retained; never an authorization or writer
identity. Tests use disposable SQLite only and do not retry external writes.
"""

import pytest

from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore
from ark.memory import sqlite_event_prefix_review as prefix


def _store(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "event-constructor-custody.sqlite",
        clock_ms=lambda: 1000,
    )
    store.put(MemoryWrite(MemoryScope("owner"), "fixture", "private"))
    return store


@pytest.mark.parametrize("epoch", ("preinstalled", "event_hash_callback"))
def test_witness_constructor_substitution_refused_without_invocation(
    tmp_path, monkeypatch, epoch,
):
    store = _store(tmp_path)
    invoked = []

    def counterfeit(self, *args, **kwargs):
        invoked.append((args, kwargs))
        raise AssertionError("injected witness constructor executed")

    if epoch == "preinstalled":
        monkeypatch.setattr(prefix.MemoryEventPrefixWitness, "__init__", counterfeit)
    else:
        original_charge = prefix._charge

        def inject_after_hash(hasher, event):
            original_charge(hasher, event)
            monkeypatch.setattr(
                prefix.MemoryEventPrefixWitness, "__init__", counterfeit,
            )

        monkeypatch.setattr(prefix, "_charge", inject_after_hash)

    with pytest.raises(
        prefix.MemoryEventPrefixRejected,
        match="retained event witness authority changed",
    ):
        prefix.capture_local_memory_event_prefix(store)
    assert invoked == []


@pytest.mark.parametrize("epoch", ("preinstalled", "comparison_digest_callback"))
def test_comparison_constructor_substitution_refused_without_invocation(
    tmp_path, monkeypatch, epoch,
):
    store = _store(tmp_path)
    retained = prefix.capture_local_memory_event_prefix(store)
    invoked = []

    def counterfeit(self, *args, **kwargs):
        invoked.append((args, kwargs))
        raise AssertionError("injected comparison constructor executed")

    if epoch == "preinstalled":
        monkeypatch.setattr(prefix.MemoryEventPrefixComparison, "__init__", counterfeit)
    else:
        original_sha256 = prefix.hashlib.sha256

        def inject_on_comparison_digest(data=b""):
            if data.startswith(prefix._COMPARISON_DOMAIN):
                monkeypatch.setattr(
                    prefix.MemoryEventPrefixComparison, "__init__", counterfeit,
                )
            return original_sha256(data)

        monkeypatch.setattr(prefix.hashlib, "sha256", inject_on_comparison_digest)

    with pytest.raises(
        prefix.MemoryEventPrefixRejected,
        match="event prefix comparison authority changed",
    ):
        prefix.compare_local_memory_event_prefix(store, retained)
    assert invoked == []


def test_clean_event_prefix_still_advances_without_authority(tmp_path):
    store = _store(tmp_path)
    retained = prefix.capture_local_memory_event_prefix(store)
    store.put(MemoryWrite(MemoryScope("owner"), "fixture-two", "private 2"))
    result = prefix.compare_local_memory_event_prefix(store, retained)
    assert result.status == "ADVANCED_PREFIX_UNAUTHENTICATED"
    assert result.previous_event_count == 1
    assert result.current_event_count == 2
    assert result.historical_writer_authenticated is False
    assert result.independent_witness_custody_proven is False
    assert result.memory_disclosure_authorized is False
    assert result.action_authorized is False
