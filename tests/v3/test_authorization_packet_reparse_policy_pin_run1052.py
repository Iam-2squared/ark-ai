"""The V3 authorization-packet writer must fail closed on reparse-policy drift."""

from __future__ import annotations

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.learning import authorization


def test_reparse_policy_rebinding_is_rejected_before_metadata_access(monkeypatch):
    class Metadata:
        st_mode = stat.S_IFDIR | 0o755

        @property
        def st_file_attributes(self):
            raise AssertionError("metadata inspected after policy rebinding")

    monkeypatch.setattr(authorization, "_REPARSE_POINT_ATTRIBUTE", 0)
    with pytest.raises(ValueError, match="reparse-point policy changed"):
        authorization._is_reparse_point(Metadata())


@pytest.mark.parametrize("attributes", (True, None, "1024", 1024.0))
def test_malformed_reparse_attribute_carrier_fails_closed(attributes):
    metadata = SimpleNamespace(
        st_mode=stat.S_IFREG | 0o600,
        st_file_attributes=attributes,
    )
    with pytest.raises(ValueError, match="reparse metadata is malformed"):
        authorization._is_reparse_point(metadata)


def test_absent_platform_attribute_uses_non_reparse_default():
    metadata = SimpleNamespace(st_mode=stat.S_IFREG | 0o600)
    assert authorization._is_reparse_point(metadata) is False


def test_packet_writer_rejects_rebound_policy_before_open(tmp_path, monkeypatch):
    target = tmp_path / "authorization-review.json"
    monkeypatch.setattr(authorization, "_REPARSE_POINT_ATTRIBUTE", 0)

    def forbidden_open(*args, **kwargs):
        raise AssertionError("packet opened after reparse policy drift")

    monkeypatch.setattr(Path, "open", forbidden_open)
    with pytest.raises(ValueError, match="reparse-point policy changed"):
        authorization._write_new_authorization_packet(
            target, {"candidate_created": False},
        )
    assert not target.exists()
