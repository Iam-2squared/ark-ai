"""A local path metadata probe is a denial-only diagnostic, not trust."""

from dataclasses import replace

import pytest

from ark.disconnected_local_source_pin import (
    DisconnectedSourcePin,
    DisconnectedSourceRejected,
    capture_disconnected_source,
    review_disconnected_source,
)

_DENIALS = (
    "independently_attested",
    "contents_verified",
    "memory_release_authorized",
    "file_mutation_authorized",
)


def _source(tmp_path):
    file = tmp_path / "synthetic.db"
    file.write_bytes(b"synthetic only")
    return file


@pytest.mark.parametrize("name", _DENIALS)
def test_false_only_replaced_authority_property_is_rejected(
    tmp_path, monkeypatch, name,
):
    file = _source(tmp_path)
    retained = capture_disconnected_source(file)
    monkeypatch.setattr(
        DisconnectedSourcePin, name, property(lambda self: False),
    )
    with pytest.raises(DisconnectedSourceRejected, match="acquired authority"):
        capture_disconnected_source(file)
    with pytest.raises(DisconnectedSourceRejected, match="acquired authority"):
        review_disconnected_source(file, retained)


def test_dataclass_equality_true_does_not_hide_stale_inode(
    tmp_path, monkeypatch,
):
    file = _source(tmp_path)
    retained = capture_disconnected_source(file)
    stale = replace(retained, file_inode=retained.file_inode + 1)
    monkeypatch.setattr(
        DisconnectedSourcePin, "__eq__", lambda self, other: True,
    )
    with pytest.raises(DisconnectedSourceRejected, match="identity"):
        review_disconnected_source(file, stale)


def test_dataclass_equality_false_does_not_disrupt_valid_local_probe(
    tmp_path, monkeypatch,
):
    file = _source(tmp_path)
    retained = capture_disconnected_source(file)
    monkeypatch.setattr(
        DisconnectedSourcePin, "__eq__", lambda self, other: False,
    )
    new = capture_disconnected_source(file)
    replay = review_disconnected_source(file, retained)
    assert new.file_inode == replay.file_inode == retained.file_inode
    assert replay.contents_verified is False
    assert replay.memory_release_authorized is False
