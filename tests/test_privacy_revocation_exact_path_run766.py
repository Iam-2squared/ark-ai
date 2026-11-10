"""Synthetic privacy-veto paths must have inert, exact pathlib carriers.

Path subclasses may implement executable parents/resolve/stat hooks. Reject
them before any filesystem access or SQLite open, including cold recovery.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from ark.memory import MemoryScope
from ark.personal_context_revocation_review import (
    SyntheticContextRevocationLedger,
    SyntheticContextRevocationRejected,
    _check_local_revocation_path,
)


class TrappedPath(type(Path("."))):
    @property
    def parents(self):
        raise AssertionError("untrusted path ancestor getter executed")

    def resolve(self, *args, **kwargs):
        raise AssertionError("untrusted path resolve executed")

    def is_symlink(self):
        raise AssertionError("untrusted path symlink query executed")


@pytest.mark.parametrize("require_existing", (False, True))
def test_reject_path_subclass_before_filesystem_access(
    tmp_path: Path, require_existing: bool,
) -> None:
    path = tmp_path / "private-veto.sqlite"
    untrusted = TrappedPath(str(path))
    assert isinstance(untrusted, Path)
    with pytest.raises(TypeError, match="exact local pathlib.Path"):
        SyntheticContextRevocationLedger(
            untrusted, require_existing=require_existing,
        )
    assert not path.exists()


def test_internal_revocation_path_guard_rejects_subclass_before_getter(
    tmp_path: Path,
) -> None:
    with pytest.raises(
        SyntheticContextRevocationRejected, match="exact local Path",
    ):
        _check_local_revocation_path(
            TrappedPath(str(tmp_path / "private-veto.sqlite")),
        )


def test_retargeted_subclass_cannot_reenter_existing_ledger(
    tmp_path: Path,
) -> None:
    path = tmp_path / "veto.sqlite"
    ledger = SyntheticContextRevocationLedger(path)
    ledger.path = TrappedPath(str(path))
    ledger._source_path = ledger.path
    with pytest.raises(
        SyntheticContextRevocationRejected, match="source path changed",
    ):
        ledger.assert_not_revoked((MemoryScope("fixture-owner", "profile"),))
