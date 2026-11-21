"""Fail closed on sidecar aliases without misclassifying a transient unlink.

All observations are fixture-only; the tests do not authorize a notification,
execution, retry or trusted filesystem identity.
"""

import os
import stat

import pytest

from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerRejected,
    _refuse_aliased_proactive_path,
)


def test_unlinked_regular_journal_is_resampled_once(tmp_path, monkeypatch):
    path = tmp_path / "journal.sqlite3"
    SyntheticProactiveLedger(path)
    sidecar = path.with_name(path.name + "-journal")
    sidecar.write_bytes(b"synthetic transient journal")
    path_type = type(path)
    original_lstat = path_type.lstat
    visits = 0

    def lstat_with_unlink(candidate, *args, **kwargs):
        nonlocal visits
        if candidate == sidecar:
            visits += 1
            if visits == 1:
                observed = original_lstat(candidate, *args, **kwargs)
                # Model a concurrent unlink after pathname lookup: a regular
                # inode with zero links must never be used without recheck.
                sidecar.unlink()
                fields = list(observed)
                fields[3] = 0
                return os.stat_result(fields)
        return original_lstat(candidate, *args, **kwargs)

    monkeypatch.setattr(path_type, "lstat", lstat_with_unlink)
    _refuse_aliased_proactive_path(path)
    assert visits == 2
    assert not sidecar.exists()


@pytest.mark.parametrize("suffix", ("-wal", "-shm", "-journal"))
def test_unsafe_hardlinked_sidecar_remains_rejected_without_retry(
    tmp_path, monkeypatch, suffix,
):
    path = tmp_path / "journal.sqlite3"
    SyntheticProactiveLedger(path)
    sidecar = path.with_name(path.name + suffix)
    sidecar.write_bytes(b"fixture")
    path_type = type(path)
    original_lstat = path_type.lstat
    visits = 0

    def lstat_with_hardlink(candidate, *args, **kwargs):
        nonlocal visits
        result = original_lstat(candidate, *args, **kwargs)
        if candidate == sidecar:
            visits += 1
            fields = list(result)
            assert stat.S_ISREG(fields[0])
            fields[3] = 2
            return os.stat_result(fields)
        return result

    monkeypatch.setattr(path_type, "lstat", lstat_with_hardlink)
    with pytest.raises(SyntheticTriggerRejected, match="unsafe proactive SQLite sidecar"):
        _refuse_aliased_proactive_path(path)
    assert visits == 1
    assert sidecar.read_bytes() == b"fixture"
