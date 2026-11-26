"""Read-only proactive history rejects redirected SQLite sources before open.

All fixtures are local and disposable. No notification, real scheduling,
trusted clock, action consent, or external ToolBackend is involved.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import ark.proactive_synthetic_continuity_review as review
from ark.proactive_synthetic_review import (
    SyntheticProactiveLedger,
    SyntheticTriggerRejected,
)


def _forbid_connect(*_args: object, **_kwargs: object) -> None:
    raise AssertionError("private SQLite open occurred before path admission")


@pytest.mark.parametrize("alias_type", ("symlink", "hardlink"))
def test_rebound_alias_never_opens_private_sqlite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, alias_type: str,
) -> None:
    source = tmp_path / "original.sqlite"
    ledger = SyntheticProactiveLedger(source)
    initial = review.read_proactive_witness(ledger)
    assert initial.row_hashes == ()

    alias = tmp_path / "alternate.sqlite"
    try:
        if alias_type == "symlink":
            alias.symlink_to(source)
        else:
            os.link(source, alias)
    except (OSError, NotImplementedError) as exc:
        pytest.skip(f"filesystem alias unavailable: {exc}")
    ledger.path = alias

    with monkeypatch.context() as patch:
        patch.setattr(review.sqlite3, "connect", _forbid_connect)
        with pytest.raises(
            SyntheticTriggerRejected, match="unsafe proactive SQLite file",
        ):
            review.read_proactive_witness(ledger, retained=initial)
    ledger.path = source
    if alias_type == "hardlink":
        # Removing a local test alias is not an ARK production operation.
        alias.unlink()
    assert review.read_proactive_witness(ledger, retained=initial) == initial


def test_replaced_path_preflight_is_denied_before_sqlite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    ledger = SyntheticProactiveLedger(tmp_path / "preflight.sqlite")
    with monkeypatch.context() as patch:
        patch.setattr(review, "_refuse_aliased_proactive_path", lambda *_: None)
        patch.setattr(review.sqlite3, "connect", _forbid_connect)
        with pytest.raises(
            SyntheticTriggerRejected,
            match="proactive witness carrier changed before private history access",
        ):
            review.read_proactive_witness(ledger)


class ExecutablePath(type(Path("."))):
    def __fspath__(self) -> str:
        raise AssertionError("untrusted path executable hook invoked")


def test_rebound_path_subclass_denied_before_executable_hook(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "subclass.sqlite"
    ledger = SyntheticProactiveLedger(source)
    ledger.path = ExecutablePath(str(source))
    with monkeypatch.context() as patch:
        patch.setattr(review.sqlite3, "connect", _forbid_connect)
        with pytest.raises(SyntheticTriggerRejected, match="requires a Path source"):
            review.read_proactive_witness(ledger)
