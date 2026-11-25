"""Passive packet custody notices POSIX metadata rewrites even with identical bytes.

This is a local, unauthenticated file-change diagnostic, never preflight or
training permission. Windows inode timestamp semantics are not asserted.
"""

from __future__ import annotations

import os

import pytest
from test_authorization_packet_file_review_run529 import _saved_packet

from ark.learning import authorization_packet_file_review as mod


def test_file_epoch_tracks_metadata_change_time(tmp_path):
    _, path, _ = _saved_packet(tmp_path)
    epoch = mod._file_epoch(path.stat())
    assert len(epoch) == 5
    assert epoch[-1] == (path.stat().st_ctime_ns if os.name == "posix" else 0)


@pytest.mark.skipif(os.name != "posix", reason="POSIX inode ctime semantics")
def test_identical_byte_rewrite_with_restored_mtime_is_rejected(
    tmp_path, monkeypatch,
):
    snapshot, path, digest = _saved_packet(tmp_path)
    real = mod.verify_detached_authorization_packet
    original = path.stat()

    def rewrite_after_review(*args, **kwargs):
        result = real(*args, **kwargs)
        retained_bytes = path.read_bytes()
        path.write_bytes(retained_bytes)
        os.utime(path, ns=(original.st_atime_ns, original.st_mtime_ns))
        latest = path.stat()
        if latest.st_ctime_ns == original.st_ctime_ns:
            pytest.skip("filesystem did not expose a distinguishable ctime epoch")
        assert latest.st_mtime_ns == original.st_mtime_ns
        assert path.read_bytes() == retained_bytes
        return result

    with monkeypatch.context() as patch:
        patch.setattr(
            mod, "verify_detached_authorization_packet", rewrite_after_review,
        )
        with pytest.raises(
            mod.LocalPacketBindingRejected, match="changed during binding",
        ):
            mod.verify_local_authorization_packet_file(
                snapshot, path, retained_packet_file_sha256=digest,
            )
