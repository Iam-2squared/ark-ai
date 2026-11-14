"""Cross-owner retained Memory prefix rejects callbacks before private event hashing.

Disposable local SQLite only. These checks do not authenticate retained
witness custody, defend an in-process adversary, or permit Memory disclosure.
"""

import pytest

from ark.memory import sqlite_event_prefix_review as prefix
from ark.memory import synthetic_multiscope_integrity_review as multiscope
from ark.memory.contracts import MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture(tmp_path):
    store = SQLiteMemoryStore(
        tmp_path / "global-prefix-codec.sqlite", clock_ms=lambda: 300,
    )
    selected = MemoryScope("selected-owner", "chosen")
    other = MemoryScope("another-owner", "private")
    store.put(MemoryWrite(selected, "source", "private selected"))
    store.put(MemoryWrite(other, "source", "private foreign"))
    witness = prefix.capture_local_memory_event_prefix(store)
    return store, selected, other, witness


@pytest.mark.parametrize(
    "path",
    (
        "imported_charge", "module_charge", "imported_epoch",
        "module_epoch", "imported_gate", "module_gate",
        "sha256", "json_dumps",
    ),
)
def test_rebound_hash_or_prefix_helper_is_denied_before_sqlite(
    tmp_path, monkeypatch, path,
):
    store, chosen, _, witness = _fixture(tmp_path)
    callback_calls = []
    read_calls = []

    def poisoned(*args, **kwargs):
        callback_calls.append(path)
        raise AssertionError("untrusted callback reached private Memory history")

    def denied_read(_self):
        read_calls.append(path)
        raise AssertionError("SQLite opened despite changed hash callback")

    target, name = {
        "imported_charge": (multiscope, "_charge_global_prefix"),
        "module_charge": (prefix, "_charge"),
        "imported_epoch": (multiscope, "_global_prefix_epoch"),
        "module_epoch": (prefix, "_witness_epoch"),
        "imported_gate": (multiscope, "_require_original_prefix_protocol"),
        "module_gate": (prefix, "_require_original_prefix_protocol"),
        "sha256": (multiscope.hashlib, "sha256"),
        "json_dumps": (multiscope.json, "dumps"),
    }[path]
    with monkeypatch.context() as patch:
        patch.setattr(target, name, poisoned)
        patch.setattr(SQLiteMemoryStore, "_connect_readonly", denied_read)
        with pytest.raises(
            multiscope.SyntheticMemorySnapshotRejected,
            match="retained global Memory event prefix codec changed",
        ):
            multiscope.review_synthetic_memory_scopes(
                store, (chosen,), retained_global_prefix=witness,
            )
    assert read_calls == []
    assert callback_calls == []


def test_rebind_during_sqlite_open_is_denied_before_foreign_callback(
    tmp_path, monkeypatch,
):
    store, chosen, _, witness = _fixture(tmp_path)
    original_open = SQLiteMemoryStore._connect_readonly
    malicious_calls = []

    def untrusted_charge(*args):
        malicious_calls.append(args)
        raise AssertionError("foreign event passed to substituted codec")

    def rebinding_open(source):
        connection = original_open(source)
        monkeypatch.setattr(prefix, "_charge", untrusted_charge)
        return connection

    with monkeypatch.context() as patch:
        patch.setattr(SQLiteMemoryStore, "_connect_readonly", rebinding_open)
        with pytest.raises(
            multiscope.SyntheticMemorySnapshotRejected,
            match="retained global Memory event prefix codec changed",
        ):
            multiscope.review_synthetic_memory_scopes(
                store, (chosen,), retained_global_prefix=witness,
            )
    assert malicious_calls == []


def test_intact_codec_remains_denial_only_after_foreign_append(tmp_path):
    store, chosen, other, witness = _fixture(tmp_path)
    earlier = multiscope.review_synthetic_memory_scopes(
        store, (chosen,), retained_global_prefix=witness,
    )
    store.put(MemoryWrite(other, "new source", "another private event"))
    current = multiscope.review_synthetic_memory_scopes(
        store, (chosen,), retained_global_prefix=witness,
    )
    assert current.snapshot_digest == earlier.snapshot_digest
    assert current.external_disclosure_authorized is False
    assert current.context_use_authorized is False
    assert current.deletion_authorized is False
