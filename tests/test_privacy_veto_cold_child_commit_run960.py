"""Run960: a post-commit process exit does not erase a privacy veto.

Only digest-only disposable SQLite fixtures are used. A same-file witness
is not authenticated consent, independent custody or deletion evidence.
"""

from __future__ import annotations

import subprocess
import sys

import pytest

from ark.disconnected_privacy_veto import (
    DisconnectedPrivacyVetoLedger,
    OfflinePrivacyVetoRejected,
)

_CHILD = """
import os
import sys
from pathlib import Path
from ark.disconnected_privacy_veto import DisconnectedPrivacyVetoLedger
ledger = DisconnectedPrivacyVetoLedger(Path(sys.argv[1]), require_existing=True)
retained = ledger.witness()
result = ledger.veto(
    owner_sha256=sys.argv[2], scope_sha256=sys.argv[3],
    observed_now_ms=100, retained=retained,
)
assert result.witness is not None and result.witness.count == 1
os._exit(62)
"""


@pytest.mark.parametrize("child_owner", ("a" * 64, "b" * 64))
def test_cold_child_veto_commit_survives_exit_and_blocks_stale_writer(
    tmp_path, child_owner: str,
) -> None:
    path = tmp_path / "privacy-child.sqlite"
    scope = "c" * 64
    unrelated = "d" * 64
    competing_owner = ("b" if child_owner.startswith("a") else "a") * 64
    parent = DisconnectedPrivacyVetoLedger(path)
    obsolete = parent.witness()
    assert obsolete.count == 0

    child = subprocess.run(
        [sys.executable, "-c", _CHILD, str(path), child_owner, scope],
        check=False, capture_output=True, text=True, timeout=25,
    )
    assert child.returncode == 62, child.stderr

    # A parent that retained the prior global witness cannot append or
    # project scope state on the basis of its stale view.
    with pytest.raises(OfflinePrivacyVetoRejected):
        parent.veto(
            owner_sha256=competing_owner, scope_sha256=scope,
            observed_now_ms=101, retained=obsolete,
        )
    with pytest.raises(OfflinePrivacyVetoRejected):
        parent.review(
            owner_sha256=child_owner, scope_sha256=scope, retained=obsolete,
        )

    cold = DisconnectedPrivacyVetoLedger(path, require_existing=True)
    new_witness = cold.witness()
    assert new_witness.count == 1
    assert new_witness != obsolete
    denied = cold.review(
        owner_sha256=child_owner, scope_sha256=scope, retained=new_witness,
    )
    unseen = cold.review(
        owner_sha256=competing_owner, scope_sha256=unrelated,
        retained=new_witness,
    )
    assert denied.local_veto_seen is True
    assert unseen.local_veto_seen is False
    for result in (denied, unseen):
        assert result.context_release_authorized is False
        assert result.consent_verified is False
        assert result.user_identity_authenticated is False
    assert new_witness.independent_custody_verified is False
