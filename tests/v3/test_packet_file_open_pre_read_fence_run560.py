"""V3 passive packet open must not read a raced nonregular inode.

No model, GPU, preflight, Candidate, protected scorer or paid compute is
accessed. POSIX FIFO defense remains platform-specific and non-authorizing.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from test_authorization_packet_file_review_run529 import _saved_packet

from ark.learning import authorization_packet_file_review as mod


@pytest.mark.skipif(not hasattr(os, "O_NONBLOCK"), reason="nonblocking open unavailable")
def test_packet_open_uses_nonblocking_flag_on_supported_system(tmp_path, monkeypatch):
    snapshot, path, digest = _saved_packet(tmp_path)
    native_open = mod.os.open
    flags_seen = []

    def record(file, flags, *args, **kwargs):
        if Path(file) == path:
            flags_seen.append(flags)
        return native_open(file, flags, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(mod.os, "open", record)
        receipt = mod.verify_local_authorization_packet_file(
            snapshot, path, retained_packet_file_sha256=digest,
        )
    assert len(flags_seen) >= 2
    assert all(flags & os.O_NONBLOCK for flags in flags_seen)
    assert receipt.external_compute_authorized is False


@pytest.mark.skipif(
    not hasattr(os, "O_NONBLOCK") or not hasattr(os, "mkfifo"),
    reason="POSIX nonblocking FIFO unavailable",
)
def test_fifo_swap_at_open_fails_closed_without_blocking(tmp_path, monkeypatch):
    snapshot, path, digest = _saved_packet(tmp_path)
    backup = tmp_path / "retained.json"
    native_open = mod.os.open
    swapped = []

    def swap_at_open(file, flags, *args, **kwargs):
        if Path(file) == path and not swapped:
            assert flags & os.O_NONBLOCK
            path.rename(backup)
            os.mkfifo(path)
            swapped.append(True)
        return native_open(file, flags, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(mod.os, "open", swap_at_open)
        with pytest.raises(mod.LocalPacketBindingRejected, match="changed during read"):
            mod.verify_local_authorization_packet_file(
                snapshot, path, retained_packet_file_sha256=digest,
            )
    assert swapped == [True]
    assert backup.is_file()
    assert not path.is_file()


def test_same_byte_replacement_is_rejected_before_unverified_read(
    tmp_path, monkeypatch,
):
    snapshot, path, digest = _saved_packet(tmp_path)
    backup = tmp_path / "old.json"
    substitute = tmp_path / "substitute.json"
    substitute.write_bytes(path.read_bytes())
    native_open = mod.os.open
    native_fdopen = mod.os.fdopen
    swapped = []

    class NoUnverifiedRead:
        def __init__(self, inner):
            self.inner = inner

        def __enter__(self):
            return self

        def __exit__(self, *_exc):
            self.inner.close()

        def fileno(self):
            return self.inner.fileno()

        def read(self, *_args, **_kwargs):
            raise AssertionError("substituted file was read before fstat custody")

    def swap_at_open(file, flags, *args, **kwargs):
        if Path(file) == path and not swapped:
            path.rename(backup)
            substitute.rename(path)
            swapped.append(True)
        return native_open(file, flags, *args, **kwargs)

    def trap_fdopen(fd, mode):
        return NoUnverifiedRead(native_fdopen(fd, mode))

    with monkeypatch.context() as patch:
        patch.setattr(mod.os, "open", swap_at_open)
        patch.setattr(mod.os, "fdopen", trap_fdopen)
        with pytest.raises(mod.LocalPacketBindingRejected, match="changed during read"):
            mod.verify_local_authorization_packet_file(
                snapshot, path, retained_packet_file_sha256=digest,
            )
    assert swapped == [True]
    assert backup.is_file()
