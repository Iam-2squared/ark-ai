"""A single SQLite sidecar inventory sweep must recheck held descriptors.

Only isolated synthetic byte fixtures. No SQLite write, credential or tool action.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ark import disconnected_sqlite_sidecar_custody as module
from ark.disconnected_sqlite_sidecar_custody import SQLiteSidecarCustodyRejected


@pytest.fixture(autouse=True)
def _requires_posix():
    if os.name != "posix" or not getattr(os, "O_NOFOLLOW", 0):
        pytest.skip("descriptor-relative SQLite inventory requires POSIX")


@pytest.mark.parametrize("which", ("main", "-wal", "-shm"))
def test_open_fd_change_during_last_named_stat_is_refused(tmp_path, monkeypatch, which):
    path = tmp_path / "synthetic.sqlite"
    path.write_bytes(b"detached main metadata")
    (tmp_path / (path.name + "-wal")).write_bytes(b"synthetic WAL")
    (tmp_path / (path.name + "-shm")).write_bytes(b"synthetic SHM")
    target = path if which == "main" else Path(str(path) + which)
    original_stat = module.os.stat
    did_mutate = False

    def mutate_at_end_of_named_sweep(name, *args, **kwargs):
        nonlocal did_mutate
        if (
            not did_mutate
            and name == path.name + "-journal"
            and kwargs.get("dir_fd") is not None
        ):
            did_mutate = True
            target.write_bytes(target.read_bytes() + b" altered after named stat")
        return original_stat(name, *args, **kwargs)

    # Verify the real POSIX descriptor capabilities before the synthetic
    # monkeypatch: patching os.stat also replaces its global supports_dir_fd
    # identity, which would make the unrelated platform preflight fail first.
    module._supported()
    monkeypatch.setattr(module, "_supported", lambda: None)
    monkeypatch.setattr(module.os, "stat", mutate_at_end_of_named_sweep)
    with pytest.raises(SQLiteSidecarCustodyRejected, match="open descriptor changed"):
        module._capture_once(path)
    assert did_mutate


def test_static_sidecar_descriptor_sweep_still_yields_inert_seal(tmp_path):
    path = tmp_path / "synthetic.sqlite"
    path.write_bytes(b"detached main metadata")
    (tmp_path / (path.name + "-wal")).write_bytes(b"synthetic WAL")
    value = module._capture_once(path)
    assert value.sidecars[0].present is True
    assert value.sqlite_transaction_atomicity_proven is False
    assert value.tool_execution_authorized is False
