"""Single-read coherent Memory snapshots reject phased reflected drift.

All test content is synthetic; this reviewer never authorizes context use.
"""

from pathlib import Path

import pytest

import ark.memory.coherent_snapshot_review as module
from ark.memory.contracts import MemorySchemaError, MemoryScope, MemoryWrite
from ark.memory.sqlite_store import SQLiteMemoryStore


def _fixture(tmp_path: Path):
    store = SQLiteMemoryStore(tmp_path / "snap # %.sqlite", clock_ms=lambda: 100)
    for namespace in ("one", "two"):
        store.put(MemoryWrite(
            MemoryScope("offline", namespace), f"source-{namespace}",
            f"private-{namespace}",
        ))
    return store, module.CoherentSnapshotRequest(
        "offline", ("one", "two"), text="private",
    )


def test_stable_phased_snapshot_is_content_bearing_but_not_authority(tmp_path):
    store, request = _fixture(tmp_path)
    result = module.review_coherent_snapshot(store, request)
    assert [group[0].content for group in result.records] == [
        "private-one", "private-two",
    ]
    assert module.review_coherent_snapshot(store, request).provenance_sha256 == (
        result.provenance_sha256
    )
    assert "private-" not in result.provenance_sha256


def test_request_transiently_changed_and_restored_between_rows_is_refused(
    tmp_path, monkeypatch,
):
    store, request = _fixture(tmp_path)
    original = module._record
    seen = 0

    def change(row):
        nonlocal seen
        result = original(row)
        seen += 1
        object.__setattr__(
            request, "text", "different" if seen == 1 else "private",
        )
        return result

    monkeypatch.setattr(module, "_record", change)
    with pytest.raises(MemorySchemaError, match="request changed"):
        module.review_coherent_snapshot(store, request)
    assert seen == 1


def test_source_transiently_swapped_and_restored_between_rows_is_refused(
    tmp_path, monkeypatch,
):
    store, request = _fixture(tmp_path)
    original_path = store.path
    original = module._record
    seen = 0

    def change(row):
        nonlocal seen
        result = original(row)
        seen += 1
        store.path = Path(str(original_path)) if seen == 1 else original_path
        return result

    monkeypatch.setattr(module, "_record", change)
    with pytest.raises(MemorySchemaError, match="source path changed"):
        module.review_coherent_snapshot(store, request)
    assert seen == 1
    assert original_path.exists()


def test_scope_carrier_retargeting_mid_hydration_is_refused(
    tmp_path, monkeypatch,
):
    store, request = _fixture(tmp_path)
    scopes = []
    original_init = MemoryScope.__post_init__
    original_record = module._record

    def remember(self):
        original_init(self)
        scopes.append(self)

    def retarget(row):
        record = original_record(row)
        object.__setattr__(scopes[3], "namespace", "one")
        return record

    monkeypatch.setattr(MemoryScope, "__post_init__", remember)
    monkeypatch.setattr(module, "_record", retarget)
    with pytest.raises(MemorySchemaError, match="scope changed"):
        module.review_coherent_snapshot(store, request)
    assert len(scopes) >= 2


@pytest.mark.parametrize("field", ["content", "scope"])
def test_hydrated_record_reflection_before_ranking_is_refused(
    tmp_path, monkeypatch, field,
):
    store, request = _fixture(tmp_path)
    records = []
    original_record = module._record
    original_tokens = module._tokens

    def capture(row):
        item = original_record(row)
        records.append(item)
        return item

    def change_when_scoring(value):
        if value == "private-one" and records:
            if field == "content":
                object.__setattr__(records[0], "content", "not-from-sqlite")
            else:
                object.__setattr__(records[0].scope, "namespace", "two")
        return original_tokens(value)

    monkeypatch.setattr(module, "_record", capture)
    monkeypatch.setattr(module, "_tokens", change_when_scoring)
    with pytest.raises(MemorySchemaError, match="record changed"):
        module.review_coherent_snapshot(store, request)
