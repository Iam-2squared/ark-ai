"""Memory prefix receipts are inert: reject injected False-valued getters.

Uses disposable offline SQLite databases only; these witnesses do not provide
writer authentication, memory-disclosure consent, or replay authorization.
"""

import pytest

import ark.memory.sqlite_event_prefix_review as prefix
from ark.memory import MemoryScope, MemoryWrite, SQLiteMemoryStore


def _store(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "prefix-guard.sqlite", clock_ms=lambda: 1000,
    )
    scope = MemoryScope("owner", "private")
    store.put(MemoryWrite(scope, "first", "synthetic private 1"))
    retained = prefix.capture_local_memory_event_prefix(store)
    store.put(MemoryWrite(scope, "second", "synthetic private 2"))
    return store, retained


class _ExecutableFalse:
    def __init__(self, calls):
        self.calls = calls

    def __get__(self, instance, owner=None):
        self.calls.append("getter")
        return False


@pytest.mark.parametrize("flag", prefix._WITNESS_DENIALS)
def test_witness_false_descriptor_refused_without_getter(tmp_path, monkeypatch, flag):
    store, _ = _store(tmp_path)
    calls = []
    monkeypatch.setattr(prefix._WITNESS, flag, _ExecutableFalse(calls))
    with pytest.raises(prefix.MemoryEventPrefixRejected, match="authority changed"):
        prefix.capture_local_memory_event_prefix(store)
    assert calls == []


@pytest.mark.parametrize("flag", prefix._COMPARISON_DENIALS)
def test_comparison_false_descriptor_refused_without_getter(
    tmp_path, monkeypatch, flag,
):
    store, retained = _store(tmp_path)
    calls = []
    monkeypatch.setattr(prefix._COMPARISON, flag, _ExecutableFalse(calls))
    with pytest.raises(prefix.MemoryEventPrefixRejected, match="authority changed"):
        prefix.compare_local_memory_event_prefix(store, retained)
    assert calls == []


def test_witness_field_callback_cannot_install_denial_getter(tmp_path, monkeypatch):
    store, _ = _store(tmp_path)
    calls = []
    original = prefix._WITNESS.__getattribute__
    injected = [False]

    def intercept(self, name):
        result = original(self, name)
        if name == "prefix_sha256" and not injected[0]:
            injected[0] = True
            monkeypatch.setattr(
                prefix._WITNESS, "action_authorized", _ExecutableFalse(calls),
            )
        return result

    monkeypatch.setattr(prefix._WITNESS, "__getattribute__", intercept)
    with pytest.raises(prefix.MemoryEventPrefixRejected, match="authority changed"):
        prefix.capture_local_memory_event_prefix(store)
    # Rebound class hooks now fail before the injected field accessor runs.
    assert injected == [False]
    assert calls == []


def test_comparison_field_callback_cannot_install_denial_getter(
    tmp_path, monkeypatch,
):
    store, retained = _store(tmp_path)
    calls = []
    original = prefix._COMPARISON.__getattribute__
    injected = [False]

    def intercept(self, name):
        result = original(self, name)
        if name == "comparison_sha256" and not injected[0]:
            injected[0] = True
            monkeypatch.setattr(
                prefix._COMPARISON, "action_authorized", _ExecutableFalse(calls),
            )
        return result

    monkeypatch.setattr(prefix._COMPARISON, "__getattribute__", intercept)
    with pytest.raises(prefix.MemoryEventPrefixRejected, match="authority changed"):
        prefix.compare_local_memory_event_prefix(store, retained)
    # Rebound class hooks now fail before the injected field accessor runs.
    assert injected == [False]
    assert calls == []


def test_original_retained_prefix_survives_append_without_authority(tmp_path):
    store, retained = _store(tmp_path)
    result = prefix.compare_local_memory_event_prefix(store, retained)
    assert result.previous_event_count == 1
    assert result.current_event_count == 2
    assert result.historical_writer_authenticated is False
    assert result.independent_witness_custody_proven is False
    assert result.memory_disclosure_authorized is False
    assert result.action_authorized is False
