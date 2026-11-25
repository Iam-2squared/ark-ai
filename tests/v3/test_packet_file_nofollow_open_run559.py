"""Passive V3 packet rereads deny final-component symlink swaps on POSIX.

These checks do not authenticate identity or authorize preflight, training,
protected V2 evaluation, paid compute, Candidate generation, or promotion.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from test_authorization_packet_file_review_run529 import _saved_packet

from ark.learning import authorization_packet_file_review as mod


@pytest.mark.skipif(not hasattr(os, "O_NOFOLLOW"), reason="O_NOFOLLOW unavailable")
def test_passive_packet_read_opens_with_kernel_nofollow(tmp_path, monkeypatch):
    snapshot, path, digest = _saved_packet(tmp_path)
    native_open = mod.os.open
    observed = []

    def record_open(file, flags, *args, **kwargs):
        if Path(file) == path:
            observed.append(flags)
        return native_open(file, flags, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(mod.os, "open", record_open)
        report = mod.verify_local_authorization_packet_file(
            snapshot, path, retained_packet_file_sha256=digest,
        )
    assert len(observed) >= 2
    assert all(flags & os.O_NOFOLLOW for flags in observed)
    assert report.external_compute_authorized is False
    assert report.candidate_generation_authorized is False
    assert report.protected_evaluation_authorized is False
    assert report.main_merge_authorized is False


@pytest.mark.skipif(not hasattr(os, "O_NOFOLLOW"), reason="O_NOFOLLOW unavailable")
def test_last_moment_final_symlink_swap_fails_before_read(tmp_path, monkeypatch):
    snapshot, path, digest = _saved_packet(tmp_path)
    backup = tmp_path / "retained-original.json"
    target = tmp_path / "synthetic-other.json"
    target.write_bytes(path.read_bytes())
    native_open = mod.os.open
    swapped = []

    def replace_at_open(file, flags, *args, **kwargs):
        if Path(file) == path and not swapped:
            path.rename(backup)
            try:
                path.symlink_to(target)
            except (OSError, NotImplementedError):
                pytest.skip("symlinks unavailable on this filesystem")
            swapped.append(True)
        return native_open(file, flags, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(mod.os, "open", replace_at_open)
        with pytest.raises(mod.LocalPacketBindingRejected, match="cannot be read"):
            mod.verify_local_authorization_packet_file(
                snapshot, path, retained_packet_file_sha256=digest,
            )
    assert swapped == [True]
    assert backup.is_file()
    assert path.is_symlink()
