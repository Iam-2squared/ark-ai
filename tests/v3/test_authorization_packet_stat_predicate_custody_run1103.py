"""Run1103: V3 authorization packet path predicates retain import identity.

Synthetic filesystem metadata only. No GPU, Candidate, paid service, protected
evaluation, or external action is invoked.
"""

from __future__ import annotations

import stat
from pathlib import Path
from types import SimpleNamespace

import pytest

from ark.learning import authorization


class _PoisonMetadata:
    @property
    def st_mode(self):
        raise AssertionError("filesystem metadata read before stat policy check")

    @property
    def st_file_attributes(self):
        raise AssertionError("filesystem metadata read before stat policy check")


def test_replaced_stat_module_is_rejected_before_metadata_access(monkeypatch):
    replacement = SimpleNamespace(
        S_ISLNK=lambda _mode: False,
        S_ISREG=lambda _mode: True,
    )
    monkeypatch.setattr(authorization, "stat", replacement)

    with pytest.raises(ValueError, match="stat module changed"):
        authorization._is_reparse_point(_PoisonMetadata())


@pytest.mark.parametrize("predicate", ("S_ISLNK", "S_ISREG"))
def test_replaced_stat_predicate_is_rejected_before_metadata_access(
    monkeypatch, predicate,
):
    monkeypatch.setattr(authorization.stat, predicate, lambda _mode: False)

    with pytest.raises(ValueError, match="stat predicate policy changed"):
        authorization._is_reparse_point(_PoisonMetadata())


def test_writer_checks_stat_predicates_before_any_path_metadata(
    tmp_path, monkeypatch,
):
    target = tmp_path / "authorization-review.json"
    metadata_calls = []

    def forbidden_lstat(_path):
        metadata_calls.append("lstat")
        raise AssertionError("path metadata read before stat policy check")

    monkeypatch.setattr(authorization.stat, "S_ISREG", lambda _mode: False)
    monkeypatch.setattr(Path, "lstat", forbidden_lstat)

    with pytest.raises(ValueError, match="stat predicate policy changed"):
        authorization._write_new_authorization_packet(
            target,
            {"candidate_created": False},
        )

    assert metadata_calls == []
