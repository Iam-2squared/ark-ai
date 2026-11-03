"""A passive review must verify the opened packet inode AFTER the read.

A path's restored metadata alone cannot attest to the byte epoch of an
already-open handle. These are synthetic files, not training authorizations.
"""

from __future__ import annotations

import os
from types import SimpleNamespace

import pytest

from ark.learning import authorization_packet_file_review as review


def test_normal_bounded_packet_byte_read_has_a_postread_handle_fence(
    tmp_path, monkeypatch,
):
    path = tmp_path / "read-only-packet.json"
    path.write_bytes(b"{}")
    original = os.fstat
    observed = []

    def counted(fd):
        observed.append(fd)
        return original(fd)

    with monkeypatch.context() as patch:
        patch.setattr(review.os, "fstat", counted)
        payload, identity = review._read_exact_local_packet(path)

    assert payload == b"{}"
    assert len(identity) == 5
    assert len(observed) == 2
    assert path.read_bytes() == b"{}"


@pytest.mark.parametrize("field", ("st_mtime_ns", "st_ino", "st_nlink"))
def test_postread_open_handle_change_is_rejected_even_if_path_is_unchanged(
    tmp_path, monkeypatch, field,
):
    path = tmp_path / "passive-packet.json"
    path.write_bytes(b'{"version":1}')
    original = os.fstat
    calls = []

    def changed_second_handle_stat(fd):
        observed = original(fd)
        calls.append(fd)
        if len(calls) != 2:
            return observed
        names = (
            "st_dev", "st_ino", "st_size", "st_mtime_ns",
            "st_ctime_ns", "st_mode", "st_nlink",
        )
        values = {name: getattr(observed, name) for name in names}
        values[field] += 1
        return SimpleNamespace(**values)

    with monkeypatch.context() as patch:
        patch.setattr(review.os, "fstat", changed_second_handle_stat)
        with pytest.raises(
            review.LocalPacketBindingRejected, match="changed during read",
        ):
            review._read_exact_local_packet(path)

    assert len(calls) == 2
    assert path.read_bytes() == b'{"version":1}'
