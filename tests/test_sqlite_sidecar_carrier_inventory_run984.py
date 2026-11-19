"""Import-time policy inventories must not be shortened before sidecar inspection.

Synthetic metadata only: no SQLite connection, data content or real action.
"""

from __future__ import annotations

import pytest

from ark import disconnected_sqlite_sidecar_custody as mod


@pytest.mark.parametrize(
    "vector_name",
    (
        "_STATE_FIELDS", "_SEAL_FIELDS", "_DENIAL_FIELDS", "_CARRIER_HOOKS",
        "_STATE_ORIGINALS", "_SEAL_ORIGINALS",
    ),
)
@pytest.mark.parametrize("mutation", ("shorten", "reverse", "equal_rebind"))
def test_sidecar_carrier_vector_rebinding_denied_before_any_probe(
    tmp_path, monkeypatch, vector_name, mutation,
):
    original = getattr(mod, vector_name)
    replacement = {
        "shorten": original[:-1],
        "reverse": original[::-1],
        "equal_rebind": tuple(list(original)),
    }[mutation]
    assert replacement is not original
    probes = []

    def forbidden_probe(_path):
        probes.append("filesystem")
        raise AssertionError("altered carrier vector reached filesystem")

    with monkeypatch.context() as patch:
        patch.setattr(mod, vector_name, replacement)
        patch.setattr(mod, "_capture_once", forbidden_probe)
        with pytest.raises(
            mod.SQLiteSidecarCustodyRejected, match="carrier definition changed",
        ):
            mod.capture_disconnected_sqlite_sidecars(tmp_path / "missing.sqlite")
    assert not probes


def test_missing_denial_field_cannot_hide_hostile_property(tmp_path, monkeypatch):
    accessed = []

    def forged_consent(_seal):
        accessed.append("forged getter")
        return True

    with monkeypatch.context() as patch:
        patch.setattr(mod, "_DENIAL_FIELDS", mod._DENIAL_FIELDS[:-2])
        patch.setattr(
            mod.DetachedSQLiteSidecarSeal, "consent_verified",
            property(forged_consent),
        )
        with pytest.raises(
            mod.SQLiteSidecarCustodyRejected, match="carrier definition changed",
        ):
            mod.capture_disconnected_sqlite_sidecars(tmp_path / "missing.sqlite")
    assert accessed == []


def test_untampered_inert_sidecar_seal_still_parses():
    sidecars = tuple(
        mod.DetachedSQLiteSidecarState(suffix, False, None)
        for suffix in ("-wal", "-shm", "-journal")
    )
    seal = mod.DetachedSQLiteSidecarSeal(
        "a" * 64, "b" * 64, "c" * 64, sidecars, "d" * 64,
    )
    result = mod._seal_snapshot(seal)
    assert result[:4] == ("a" * 64, "b" * 64, "c" * 64, "d" * 64)
    assert seal.consent_verified is False
    assert seal.tool_execution_authorized is False
