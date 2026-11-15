"""Reject malformed synthetic privacy-veto SQLite paths before filesystem access.

All tests operate on disposable names only; no actual consent, live Memory,
real account path or revocation authority is involved.
"""

from pathlib import Path

import pytest

from ark.disconnected_privacy_veto import (
    DisconnectedPrivacyVetoLedger,
    OfflinePrivacyVetoRejected,
    genesis_privacy_veto_witness,
)


@pytest.mark.parametrize(
    ("label", "message"),
    (
        ("veto\\x00.sqlite", "exact absolute fixture path required"),
        ("veto\\ud800.sqlite", "fixture path is not valid UTF-8"),
    ),
)
def test_invalid_lexical_path_fails_before_any_stat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, label: str, message: str,
) -> None:
    # Decode only the controlled test spelling, never a real filesystem name.
    invalid_name = label.encode("ascii").decode("unicode_escape")
    invalid = tmp_path / invalid_name
    called: list[str] = []

    def unexpected_lstat(*_args: object, **_kwargs: object) -> object:
        called.append("lstat")
        raise AssertionError("invalid lexical name reached filesystem")

    with monkeypatch.context() as patch:
        patch.setattr(type(tmp_path), "lstat", unexpected_lstat)
        with pytest.raises(OfflinePrivacyVetoRejected, match=message):
            DisconnectedPrivacyVetoLedger(invalid)

    assert called == []


def test_multibyte_path_budget_includes_longest_sqlite_sidecar(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    # The codepoint count is small enough to pass the historical len(str)
    # guard, while UTF-8 bytes plus '-journal' exceed the SQLite path budget.
    prefix_bytes = len(str(tmp_path).encode("utf-8")) + 1
    count = 1 + (4096 - prefix_bytes - len(".sqlite") - len("-journal")) // 3
    invalid = tmp_path / ("界" * count + ".sqlite")
    assert len(str(invalid)) < 4096
    assert len(str(invalid).encode("utf-8")) + len("-journal") > 4096
    called: list[str] = []

    def unexpected_lstat(*_args: object, **_kwargs: object) -> object:
        called.append("lstat")
        raise AssertionError("oversize path reached filesystem")

    with monkeypatch.context() as patch:
        patch.setattr(type(tmp_path), "lstat", unexpected_lstat)
        with pytest.raises(
            OfflinePrivacyVetoRejected, match="fixture SQLite path budget exceeded",
        ):
            DisconnectedPrivacyVetoLedger(invalid)

    assert called == []


def test_valid_disconnected_privacy_ledger_remains_restart_readable(
    tmp_path: Path,
) -> None:
    path = tmp_path / "veto.sqlite"
    first = DisconnectedPrivacyVetoLedger(path)
    expected = genesis_privacy_veto_witness()
    assert first.witness() == expected
    restarted = DisconnectedPrivacyVetoLedger(path, require_existing=True)
    assert restarted.witness() == expected
