"""Native SQLite pathname admission for disconnected WRITE/audit fixtures.

No tool executor or authorization is involved. Overlong native filesystem
names and NULs must be denied before any filesystem metadata operation.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from ark.agency import disconnected_atomic_preaction_ledger as audit
from ark.agency import disconnected_write_slot_ledger as slots


@pytest.mark.parametrize("kind", ("write_slot", "atomic_preaction"))
@pytest.mark.parametrize("operation", ("create", "reopen"))
@pytest.mark.parametrize("bad_name", ("nul", "multibyte", "journal_boundary"))
def test_unsafe_path_fails_closed_before_any_lstat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
    kind: str, operation: str, bad_name: str,
) -> None:
    if bad_name == "nul":
        path = tmp_path / "disconnected\x00ledger.sqlite"
    elif bad_name == "multibyte":
        path = tmp_path / ("界" * 1400 + ".sqlite")
        assert len(str(path)) < 4096
        assert len(os.fsencode(path)) > 4096
    else:
        # Main DB fits; only its -journal sibling exceeds 4096 native bytes.
        name_size = 4096 - len(os.fsencode(tmp_path)) - 1 - 2
        path = tmp_path / ("x" * name_size)
        assert len(os.fsencode(path)) == 4094
        assert len(os.fsencode(path)) + len(b"-journal") > 4096

    called: list[str] = []

    def never_lstat(self: Path) -> object:
        called.append(str(self))
        raise AssertionError("unsafe SQLite path reached filesystem inspection")

    with monkeypatch.context() as patch:
        patch.setattr(Path, "lstat", never_lstat)
        if kind == "write_slot":
            with pytest.raises(slots.WriteSlotLedgerRejected):
                slots.DisconnectedWriteSlotLedger(
                    path, create=operation == "create",
                )
        else:
            with pytest.raises(audit.AtomicPreactionRejected):
                if operation == "create":
                    audit.DisconnectedAtomicPreactionLedger.create(path)
                else:
                    audit.DisconnectedAtomicPreactionLedger(path)
    assert called == []
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize("kind", ("write_slot", "atomic_preaction"))
def test_safe_native_path_still_creates_disconnected_ledger(
    tmp_path: Path, kind: str,
) -> None:
    path = tmp_path / "synthetic.sqlite"
    if kind == "write_slot":
        ledger = slots.DisconnectedWriteSlotLedger(path, create=True)
        assert ledger.inspect(retained=slots.genesis_write_slot_witness()).count == 0
        assert slots.DisconnectedWriteSlotLedger(path).inspect(
            retained=slots.genesis_write_slot_witness(),
        ).count == 0
    else:
        ledger = audit.DisconnectedAtomicPreactionLedger.create(path)
        prior = audit.genesis_atomic_preaction_witness()
        assert ledger.inspect(prior).witness.count == 0
        reopened = audit.DisconnectedAtomicPreactionLedger(path)
        assert reopened.inspect(prior).witness.count == 0
    assert path.is_file()
