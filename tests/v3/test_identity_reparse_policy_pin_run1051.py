"""The V3 identity manifest must fail closed if its reparse policy drifts."""

from __future__ import annotations

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

import ark.learning.identity as identity


def test_reparse_policy_rebinding_is_rejected_before_metadata_access(monkeypatch):
    class Metadata:
        st_mode = stat.S_IFDIR | 0o755

        @property
        def st_file_attributes(self):
            raise AssertionError("metadata inspected after policy rebinding")

    monkeypatch.setattr(identity, "_REPARSE_POINT_ATTRIBUTE", 0)
    with pytest.raises(ValueError, match="reparse-point policy changed"):
        identity._is_reparse_point(Metadata())


@pytest.mark.parametrize("attributes", (True, None, "1024", 1024.0))
def test_malformed_reparse_attribute_carrier_fails_closed(attributes):
    metadata = SimpleNamespace(
        st_mode=stat.S_IFREG | 0o600,
        st_file_attributes=attributes,
    )
    with pytest.raises(ValueError, match="attribute metadata is malformed"):
        identity._is_reparse_point(metadata)


def test_absent_platform_attribute_uses_non_reparse_default():
    metadata = SimpleNamespace(st_mode=stat.S_IFREG | 0o600)
    assert identity._is_reparse_point(metadata) is False


def test_file_identity_rejects_rebound_policy_before_open(tmp_path, monkeypatch):
    payload = tmp_path / "identity.bin"
    payload.write_bytes(b"synthetic identity bytes")

    monkeypatch.setattr(identity, "_REPARSE_POINT_ATTRIBUTE", 0)

    def forbidden_open(*args, **kwargs):
        raise AssertionError("identity payload opened after reparse policy drift")

    monkeypatch.setattr(Path, "open", forbidden_open)
    with pytest.raises(ValueError, match="reparse-point policy changed"):
        identity.file_identity(payload)
