"""Review-only V3 packet output must reflect its canonical bytes after write.

No user authorization, training, paid service, GPU, or Candidate is involved.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.learning import authorization as mod
from ark.learning.execution import canonical_json


def _packet():
    return {"request_scope": "REVIEW_ONLY", "full_training_authorized": False}


@pytest.mark.parametrize(
    ("mutation", "message"),
    (
        ("short", "incomplete"),
        ("same_length", "bytes or identity changed"),
    ),
)
def test_write_result_is_not_a_verified_packet(
    tmp_path, monkeypatch, mutation, message,
):
    path = tmp_path / "packet.json"
    source = _packet()
    actual_open = Path.open

    class TamperedWrite:
        def __init__(self, real):
            self.real = real

        def __enter__(self):
            self.real.__enter__()
            return self

        def __exit__(self, *args):
            return self.real.__exit__(*args)

        def write(self, data):
            if mutation == "short":
                return self.real.write(data[:-1])
            replacement = b" " + data[1:]
            assert len(replacement) == len(data)
            return self.real.write(replacement)

    def open_packet(self, mode="r", *args, **kwargs):
        opened = actual_open(self, mode, *args, **kwargs)
        if self == path and mode == "xb":
            return TamperedWrite(opened)
        return opened

    monkeypatch.setattr(Path, "open", open_packet)
    with pytest.raises(ValueError, match=message):
        mod._write_new_authorization_packet(path, source)
    assert path.exists()
    assert source["full_training_authorized"] is False


def test_readback_callback_cannot_change_review_tree(tmp_path, monkeypatch):
    path = tmp_path / "packet.json"
    source = _packet()
    actual_read = Path.read_bytes

    def corrupt_packet_after_read(self):
        data = actual_read(self)
        if self == path:
            source["full_training_authorized"] = True
        return data

    monkeypatch.setattr(Path, "read_bytes", corrupt_packet_after_read)
    with pytest.raises(ValueError, match="snapshot changed"):
        mod._write_new_authorization_packet(path, source)
    assert path.exists()


def test_postwrite_hardlink_alias_is_rejected(tmp_path, monkeypatch):
    path = tmp_path / "packet.json"
    alias = tmp_path / "alias.json"
    actual_read = Path.read_bytes

    def link_after_read(self):
        data = actual_read(self)
        if self == path:
            try:
                alias.hardlink_to(path)
            except (OSError, NotImplementedError):
                pytest.skip("filesystem does not support hardlinks")
        return data

    monkeypatch.setattr(Path, "read_bytes", link_after_read)
    with pytest.raises(ValueError, match="identity changed"):
        mod._write_new_authorization_packet(path, _packet())
    assert alias.exists()


def test_normal_exclusive_packet_still_writes_exact_review_bytes(tmp_path):
    path = tmp_path / "packet.json"
    packet = _packet()
    mod._write_new_authorization_packet(path, packet)
    assert path.read_bytes() == canonical_json(packet)
    with pytest.raises(ValueError, match="non-aliased"):
        mod._write_new_authorization_packet(path, packet)
