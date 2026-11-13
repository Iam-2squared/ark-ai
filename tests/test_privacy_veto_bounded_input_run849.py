"""Bound disconnected privacy-veto inputs before regex or private SQLite access.

All inputs and receipts are synthetic. Rejection is not user authentication,
consent, deletion evidence, or authorization to release remembered content.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

import ark.disconnected_privacy_veto as veto

OWNER = "a" * 64
SCOPE = "b" * 64


class WidthCheckedMatcher:
    """Test double: invoking a regex on an unbounded string is a failure."""

    def fullmatch(self, value: str):
        assert type(value) is str
        assert len(value) == 64
        return re.fullmatch(r"[0-9a-f]{64}\\Z", value)


@pytest.mark.parametrize(
    "invalid",
    ("", "a" * 63, "a" * 65, "A" * 64, "a" * 100_000, True, None),
)
@pytest.mark.parametrize("field", ("owner", "scope"))
@pytest.mark.parametrize("action", ("review", "veto"))
def test_untrusted_hash_rejected_before_unbounded_regex_or_sqlite(
    tmp_path: Path, monkeypatch, invalid, field: str, action: str,
) -> None:
    ledger = veto.DisconnectedPrivacyVetoLedger(tmp_path / "bounded.sqlite")
    retained = veto.genesis_privacy_veto_witness()
    opens = []

    def forbidden_open(*, read_only: bool):
        opens.append(read_only)
        raise AssertionError("invalid request must not open private SQLite")

    monkeypatch.setattr(ledger, "_open", forbidden_open)
    monkeypatch.setattr(veto, "_SHA", WidthCheckedMatcher())
    owner = invalid if field == "owner" else OWNER
    scope = invalid if field == "scope" else SCOPE
    with pytest.raises(veto.OfflinePrivacyVetoRejected, match="invalid veto"):
        if action == "review":
            ledger.review(owner_sha256=owner, scope_sha256=scope, retained=retained)
        else:
            ledger.veto(
                owner_sha256=owner,
                scope_sha256=scope,
                observed_now_ms=100,
                retained=retained,
            )
    assert opens == []


@pytest.mark.parametrize("length", (4097, 8192))
def test_oversized_fixture_path_refused_before_file_access(
    tmp_path: Path, length: int,
) -> None:
    # No OS stat/connect/alias resolution should receive the oversized name.
    path = tmp_path / ("p" * length)
    with pytest.raises(
        veto.OfflinePrivacyVetoRejected, match="exact absolute fixture path",
    ):
        veto.DisconnectedPrivacyVetoLedger(path)


def test_exact_width_offline_veto_still_persists_without_authority(
    tmp_path: Path,
) -> None:
    path = tmp_path / "bounded.sqlite"
    ledger = veto.DisconnectedPrivacyVetoLedger(path)
    retained = veto.genesis_privacy_veto_witness()
    assert ledger.review(
        owner_sha256=OWNER, scope_sha256=SCOPE, retained=retained,
    ).local_veto_seen is False
    receipt = ledger.veto(
        owner_sha256=OWNER, scope_sha256=SCOPE,
        observed_now_ms=100, retained=retained,
    )
    reopened = veto.DisconnectedPrivacyVetoLedger(path, require_existing=True)
    review = reopened.review(
        owner_sha256=OWNER, scope_sha256=SCOPE, retained=receipt.witness,
    )
    assert review.local_veto_seen is True
    assert review.consent_verified is False
    assert review.context_release_authorized is False
    assert receipt.deletion_proven is False
