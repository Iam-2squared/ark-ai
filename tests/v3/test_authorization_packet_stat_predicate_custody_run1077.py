"""The V3 review-packet path guard pins its import-original stat policy."""

from __future__ import annotations

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.learning import authorization


def _forbidden(*_args, **_kwargs):
    raise AssertionError("filesystem inspection ran before stat-policy admission")


def test_stat_module_rebinding_is_rejected_before_ancestor_lstat(tmp_path, monkeypatch):
    target = tmp_path / "authorization-review.json"
    monkeypatch.setattr(Path, "lstat", _forbidden)
    monkeypatch.setattr(
        authorization,
        "stat",
        SimpleNamespace(S_ISLNK=_forbidden, S_ISREG=_forbidden),
    )
    with pytest.raises(ValueError, match="reparse-point policy changed"):
        authorization._write_new_authorization_packet(
            target, {"candidate_created": False},
        )


@pytest.mark.parametrize("predicate", ("S_ISLNK", "S_ISREG"))
def test_stat_mode_predicate_rebinding_is_rejected_before_lstat(
    predicate, tmp_path, monkeypatch,
):
    target = tmp_path / "authorization-review.json"
    monkeypatch.setattr(Path, "lstat", _forbidden)
    monkeypatch.setattr(authorization.stat, predicate, _forbidden)
    with pytest.raises(ValueError, match="reparse-point policy changed"):
        authorization._write_new_authorization_packet(
            target, {"candidate_created": False},
        )


def test_reparse_metadata_callback_cannot_replace_predicate_before_classification(
    monkeypatch,
):
    class Metadata:
        st_file_attributes = 0

        @property
        def st_mode(self):
            monkeypatch.setattr(authorization.stat, "S_ISLNK", _forbidden)
            return stat.S_IFREG | 0o600

    with pytest.raises(ValueError, match="reparse-point policy changed"):
        authorization._is_reparse_point(Metadata())


def test_regular_file_metadata_callback_cannot_replace_predicate():
    class Metadata:
        @property
        def st_mode(self):
            authorization.stat.S_ISREG = _forbidden
            return stat.S_IFREG | 0o600

    original = authorization.stat.S_ISREG
    try:
        with pytest.raises(ValueError, match="reparse-point policy changed"):
            authorization._is_regular_file(Metadata())
    finally:
        authorization.stat.S_ISREG = original
