"""Free-only V3 execution snapshot same-file source-epoch custody.

No compute, model loading, Candidate generation or protected scorer opening.
"""

from __future__ import annotations

import json

import pytest

from ark.learning import execution as mod


def test_unchanged_noncanonical_snapshot_retains_legacy_loader_behavior(tmp_path):
    path = tmp_path / "snapshot.json"
    path.write_bytes(b'{  "x" : 1, "authorization" : {"ok": false} }\n')
    assert mod.load_snapshot(path) == {"x": 1, "authorization": {"ok": False}}


@pytest.mark.parametrize("replacement", [
    b'{"authorization":true}',
    b'{"authorization":false}',
    b'{"z":"mutated"}',
    b'{"x":"' + b"a" * 1_048_576 + b'"}',
])
def test_local_bytes_changed_during_decode_are_denied(tmp_path, monkeypatch, replacement):
    path = tmp_path / "snapshot.json"
    path.write_bytes(b'{"authorization":false}')
    original = json.loads

    def switched(*args, **kwargs):
        parsed = original(*args, **kwargs)
        path.write_bytes(replacement)
        return parsed

    monkeypatch.setattr(mod.json, "loads", switched)
    with pytest.raises(ValueError, match="source changed"):
        mod.load_snapshot(path)


def test_same_bytes_replaced_inode_during_decode_are_denied(tmp_path, monkeypatch):
    path = tmp_path / "snapshot.json"
    replacement = tmp_path / "replacement.json"
    path.write_bytes(b'{"authorization":false}')
    replacement.write_bytes(path.read_bytes())
    original = json.loads

    def switched(*args, **kwargs):
        parsed = original(*args, **kwargs)
        replacement.replace(path)
        return parsed

    monkeypatch.setattr(mod.json, "loads", switched)
    with pytest.raises(ValueError, match="source changed"):
        mod.load_snapshot(path)


def test_deleted_source_during_decode_is_denied(tmp_path, monkeypatch):
    path = tmp_path / "snapshot.json"
    path.write_bytes(b'{"authorization":false}')
    original = json.loads

    def switched(*args, **kwargs):
        parsed = original(*args, **kwargs)
        path.unlink()
        return parsed

    monkeypatch.setattr(mod.json, "loads", switched)
    with pytest.raises(ValueError, match="source changed"):
        mod.load_snapshot(path)
    assert not path.exists()
