"""Run955: startup witness slot/lookup substitution fails before private reads.

Three disposable disconnected SQLite fixtures; no actual startup, permission,
dispatch, consent, clock attestation or cross-store atomicity is inferred.
"""

from __future__ import annotations

import pytest

from ark.agency.disconnected_due_reservation import DisconnectedDueReservations
from ark.disconnected_restart_witness_bundle import (
    OfflineRestartWitnessRejected,
    review_disconnected_restart_witnesses,
)
from ark.memory.disconnected_witness_ledger import (
    DisconnectedMemoryWitnessLedger,
    genesis_memory_ledger_witness,
)
from ark.personal_context_replay_ledger import DisconnectedContextReplayLedger


@pytest.mark.parametrize(
    ("index", "name"),
    (
        (0, "epochs"),
        (0, "__getattribute__"),
        (1, "chain_sha256"),
        (1, "__getattribute__"),
        (2, "fingerprint"),
        (2, "__getattribute__"),
    ),
)
def test_original_retained_witness_descriptors_required_before_reads(
    tmp_path, monkeypatch, index: int, name: str,
) -> None:
    memory = DisconnectedMemoryWitnessLedger(tmp_path / "memory.sqlite", create=True)
    context = DisconnectedContextReplayLedger(tmp_path / "context.sqlite", create=True)
    due = DisconnectedDueReservations(tmp_path / "due.sqlite")
    retained = (
        genesis_memory_ledger_witness(), context.witness(), due.witness(),
    )

    def untrusted_read(*_args, **_kwargs):
        pytest.fail("substituted retained witness getter must never run")

    target_type = type(retained[index])
    with monkeypatch.context() as patch:
        patch.setattr(
            target_type, name,
            untrusted_read if name == "__getattribute__"
            else property(untrusted_read),
        )
        with pytest.raises(OfflineRestartWitnessRejected, match="authority"):
            review_disconnected_restart_witnesses(
                memory, retained[0], context, retained[1], due, retained[2],
            )

    # Original sealed constructors/slots are available after the injected
    # property is restored. A clean local consistency check is still inert.
    report = review_disconnected_restart_witnesses(
        memory, retained[0], context, retained[1], due, retained[2],
    )
    assert report.memory_epochs == 0
    assert report.context_requests == 0
    assert report.due_occurrences == 0
    assert report.startup_authorized is False
    assert report.dispatch_authorized is False
    assert report.automatic_replay_authorized is False
