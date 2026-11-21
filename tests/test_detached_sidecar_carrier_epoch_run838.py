"""Detached SQLite sidecar witnesses refuse class-level callback substitution.

All paths are missing or disposable local byte fixtures. No SQLite transaction,
actual Memory store, user data, permission, or ToolBackend is involved.
"""

from __future__ import annotations

import os

import pytest

from ark import disconnected_sqlite_sidecar_custody as custody


@pytest.mark.parametrize(
    ("carrier", "attribute", "descriptor"),
    (
        ("state", "__eq__", False),
        ("state", "identity_sha256", True),
        ("state", "__getattribute__", False),
        ("seal", "__eq__", False),
        ("seal", "__init__", False),
        ("seal", "fingerprint", True),
        ("seal", "consent_verified", True),
        ("seal", "tool_execution_authorized", True),
    ),
)
@pytest.mark.parametrize("operation", ("capture", "review"))
def test_replaced_carrier_rejected_before_path_or_user_callback(
    tmp_path, monkeypatch, carrier, attribute, descriptor, operation,
):
    attempted = []

    def poison(*_args, **_kwargs):
        attempted.append("carrier")
        raise AssertionError("substituted SQLite carrier callback executed")

    def forbid_source(_source):
        attempted.append("filesystem")
        raise AssertionError("filesystem inspected before carrier validation")

    klass = (
        custody.DetachedSQLiteSidecarState
        if carrier == "state" else custody.DetachedSQLiteSidecarSeal
    )
    replacement = property(poison) if descriptor else poison
    with monkeypatch.context() as patch:
        patch.setattr(klass, attribute, replacement)
        patch.setattr(custody, "_capture_once", forbid_source)
        missing = tmp_path / "synthetic-private.sqlite"
        with pytest.raises(
            custody.SQLiteSidecarCustodyRejected, match="carrier definition",
        ):
            if operation == "capture":
                custody.capture_disconnected_sqlite_sidecars(missing)
            else:
                custody.review_disconnected_sqlite_sidecars(missing, None)
    assert attempted == []
    assert not missing.exists()


@pytest.mark.skipif(
    os.name != "posix" or not getattr(os, "O_NOFOLLOW", 0),
    reason="POSIX descriptor-relative sidecar fixture only",
)
def test_forged_second_snapshot_never_runs_custom_equality(tmp_path, monkeypatch):
    path = tmp_path / "synthetic.sqlite"
    path.write_bytes(b"disposable synthetic data")
    first = custody.capture_disconnected_sqlite_sidecars(path)
    observed = []

    class Forged:
        def __eq__(self, _other):
            observed.append("compared")
            raise AssertionError("untrusted equality was invoked")

    calls = 0

    def replaced_capture(_path):
        nonlocal calls
        calls += 1
        return first if calls == 1 else Forged()

    with monkeypatch.context() as patch:
        patch.setattr(custody, "_capture_once", replaced_capture)
        with pytest.raises(
            custody.SQLiteSidecarCustodyRejected,
            match="malformed retained SQLite sidecar seal",
        ):
            custody.capture_disconnected_sqlite_sidecars(path)
    assert calls == 2
    assert observed == []


@pytest.mark.skipif(
    os.name != "posix" or not getattr(os, "O_NOFOLLOW", 0),
    reason="POSIX descriptor-relative sidecar fixture only",
)
def test_unmodified_seal_remains_stable_and_deny_only(tmp_path):
    path = tmp_path / "synthetic.sqlite"
    path.write_bytes(b"disposable synthetic data")
    seal = custody.capture_disconnected_sqlite_sidecars(path)
    reviewed = custody.review_disconnected_sqlite_sidecars(path, seal)
    assert reviewed.fingerprint == seal.fingerprint
    assert reviewed.consent_verified is False
    assert reviewed.tool_execution_authorized is False
