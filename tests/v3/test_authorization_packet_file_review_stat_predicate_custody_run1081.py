"""The read-only V3 packet verifier pins stat predicates and malformed metadata."""

from __future__ import annotations

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.learning import authorization_packet_file_review as module


def _forbidden(*_args, **_kwargs):
    raise AssertionError("packet path inspection ran before stat-policy admission")


def test_stat_module_rebinding_is_rejected_before_lstat(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "lstat", _forbidden)
    monkeypatch.setattr(
        module,
        "stat",
        SimpleNamespace(S_ISLNK=_forbidden, S_ISREG=_forbidden),
    )
    with pytest.raises(
        module.LocalPacketBindingRejected, match="reparse-point guard changed",
    ):
        module._read_exact_local_packet(tmp_path / "packet.json")


@pytest.mark.parametrize("predicate", ("S_ISLNK", "S_ISREG"))
def test_stat_predicate_rebinding_is_rejected_before_lstat(
    predicate, tmp_path, monkeypatch,
):
    monkeypatch.setattr(Path, "lstat", _forbidden)
    monkeypatch.setattr(module.stat, predicate, _forbidden)
    with pytest.raises(
        module.LocalPacketBindingRejected, match="reparse-point guard changed",
    ):
        module._read_exact_local_packet(tmp_path / "packet.json")


@pytest.mark.parametrize("attributes", (True, None, "1024", 1024.0))
def test_malformed_reparse_metadata_fails_closed(attributes):
    info = SimpleNamespace(
        st_mode=stat.S_IFREG | 0o600,
        st_file_attributes=attributes,
    )
    with pytest.raises(
        module.LocalPacketBindingRejected, match="reparse metadata is malformed",
    ):
        module._is_reparse_point(info)


def test_absent_platform_reparse_attribute_uses_zero_default():
    info = SimpleNamespace(st_mode=stat.S_IFREG | 0o600)
    assert module._is_reparse_point(info) is False


def test_mode_metadata_callback_cannot_replace_symlink_predicate(monkeypatch):
    class Metadata:
        st_file_attributes = 0

        @property
        def st_mode(self):
            monkeypatch.setattr(module.stat, "S_ISLNK", _forbidden)
            return stat.S_IFREG | 0o600

    with pytest.raises(
        module.LocalPacketBindingRejected, match="reparse-point guard changed",
    ):
        module._is_reparse_point(Metadata())


def test_regular_file_metadata_callback_cannot_replace_predicate(monkeypatch):
    class Metadata:
        @property
        def st_mode(self):
            monkeypatch.setattr(module.stat, "S_ISREG", _forbidden)
            return stat.S_IFREG | 0o600

    with pytest.raises(
        module.LocalPacketBindingRejected, match="reparse-point guard changed",
    ):
        module._is_regular_file(Metadata())
