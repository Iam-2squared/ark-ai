"""A fixture bridge must not certify mutated inputs after SQLite append.

The test intentionally induces only local synthetic callbacks. If a callback
mutates an input after COMMIT, the append remains durable: never auto-retry.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from test_disconnected_read_receipt_bridge_run478 import STEP, _case

import ark.agency.disconnected_read_journal as journal_module
import ark.agency.disconnected_read_receipt_bridge as bridge


@pytest.mark.parametrize("target", ("request", "result", "binding"))
def test_hash_callback_mutation_after_preparation_cannot_return_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, target: str,
) -> None:
    request, result, binding = _case()
    witness = journal_module.genesis_witness()
    receipt = bridge.prepare_disconnected_read_receipt(
        STEP, request, result, binding,
    )
    expected_tip = journal_module._chain(witness.tip_sha256, 1, receipt)
    real_chain = journal_module._chain
    injected = False

    def mutating_chain(
        previous: str, index: int, row: journal_module.ReadReceipt,
    ) -> str:
        nonlocal injected
        if not injected:
            injected = True
            if target == "request":
                object.__setattr__(request, "operation", "text.stats")
            elif target == "result":
                object.__setattr__(result, "canonical_result_json", "{}")
            else:
                object.__setattr__(binding, "request_bound_digest", "f" * 64)
        return real_chain(previous, index, row)

    with journal_module.DisconnectedReadJournal.create(
        tmp_path / "fixture.db"
    ) as journal:
        with monkeypatch.context() as patch:
            patch.setattr(journal_module, "_chain", mutating_chain)
            with pytest.raises(
                bridge.DisconnectedReadBridgeRejected,
                match="commit may have happened",
            ):
                bridge.append_disconnected_fixture_read(
                    journal, witness, STEP, request, result, binding,
                )
        assert injected
        # The bridge rejected the returned success, but the append already
        # committed. Repeating it is NOT a safe rollback/retry.
        retained = journal_module.ReadJournalWitness(1, expected_tip)
        assert journal.verify(retained).count == 1


def test_bridge_refuses_wrong_count_even_if_forged_append_returns_witness(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    request, result, binding = _case()
    with journal_module.DisconnectedReadJournal.create(
        tmp_path / "fixture.db"
    ) as journal:
        original = journal_module.genesis_witness()
        with monkeypatch.context() as patch:
            patch.setattr(
                journal_module.DisconnectedReadJournal,
                "append",
                lambda self, receipt, retained: original,
            )
            with pytest.raises(
                bridge.DisconnectedReadBridgeRejected,
                match="untrusted READ journal result",
            ):
                bridge.append_disconnected_fixture_read(
                    journal, original, STEP, request, result, binding,
                )
        assert journal.verify(original).count == 0
