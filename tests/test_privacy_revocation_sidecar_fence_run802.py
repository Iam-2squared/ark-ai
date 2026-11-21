"""Context revocation must reject unsafe SQLite sidecars before opening data.

These synthetic veto checks cannot authenticate consent or authorize context
disclosure, notification, remote tools, or irreversible erasure.
"""

from __future__ import annotations

import pytest

from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
)

_SUFFIXES = ("-wal", "-shm", "-journal")


@pytest.mark.parametrize("suffix", _SUFFIXES)
@pytest.mark.parametrize("kind", ("directory", "hardlink", "symlink"))
def test_alias_or_special_sidecar_refused_on_restart_and_live_read(
    tmp_path, suffix, kind,
):
    path = tmp_path / "context-veto.sqlite3"
    ledger = SyntheticContextRevocationLedger(path)
    sidecar = path.with_name(path.name + suffix)
    if kind == "directory":
        sidecar.mkdir()
    else:
        target = tmp_path / "other-private-file"
        target.write_bytes(b"not a SQLite sidecar")
        try:
            if kind == "hardlink":
                sidecar.hardlink_to(target)
            else:
                sidecar.symlink_to(target)
        except OSError as exc:
            pytest.skip(f"OS does not allow synthetic {kind} fixture: {exc}")

    with pytest.raises(
        SyntheticContextRevocationRejected, match="sidecar",
    ):
        SyntheticContextRevocationLedger(path, require_existing=True)
    with pytest.raises(
        SyntheticContextRevocationRejected, match="sidecar",
    ):
        ledger._connect(readonly=True)
    # No alias target should be modified by either rejected operation.
    if kind != "directory":
        assert target.read_bytes() == b"not a SQLite sidecar"


@pytest.mark.parametrize("suffix", _SUFFIXES)
def test_orphan_sidecar_cannot_bootstrap_new_empty_revocation_veto(tmp_path, suffix):
    path = tmp_path / "missing-veto.sqlite3"
    sidecar = path.with_name(path.name + suffix)
    sidecar.write_bytes(b"orphaned SQLite metadata")
    with pytest.raises(
        SyntheticContextRevocationRejected, match="sidecar",
    ):
        SyntheticContextRevocationLedger(path)
    assert not path.exists()
    assert sidecar.read_bytes() == b"orphaned SQLite metadata"


def test_existing_clean_veto_ledger_still_reopens_without_authority(tmp_path):
    path = tmp_path / "context-veto.sqlite3"
    original = SyntheticContextRevocationLedger(path)
    recovered = SyntheticContextRevocationLedger(path, require_existing=True)
    assert original.path == recovered.path == path
    assert not any(
        path.with_name(path.name + suffix).is_symlink() for suffix in _SUFFIXES
    )
