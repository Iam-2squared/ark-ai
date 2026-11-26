"""Synthetic due witnesses must retain the original nonauthorizing descriptor.

A locally committed reservation is not rolled back by postcommit validation.
No test grants scheduler dispatch, clock trust or notification permission.
"""

import pytest

import ark.agency.disconnected_due_reservation as due


def _ledger(tmp_path):
    ledger = due.DisconnectedDueReservations(tmp_path / "due-witness-run605.sqlite")
    return ledger, ledger.witness()


def _reserve(ledger, retained):
    return ledger.reserve_due(
        policy_sha256="a" * 64,
        due_at_ms=100,
        observed_now_ms=101,
        retained=retained,
    )


@pytest.mark.parametrize("return_value", (False, True))
def test_genesis_rejects_preinstalled_false_looking_getter_before_execution(
    monkeypatch, return_value,
):
    called = []

    def counterfeit(_self):
        called.append("getter")
        return return_value

    with monkeypatch.context() as patch:
        patch.setattr(
            due.DueReservationWitness,
            "independent_custody_proven",
            property(counterfeit),
        )
        with pytest.raises(due.DueReservationRejected, match="witness authority"):
            due.genesis_due_witness()
    assert called == []


@pytest.mark.parametrize("return_value", (False, True))
def test_retained_witness_rejects_getter_before_reservation(
    tmp_path, monkeypatch, return_value,
):
    ledger, retained = _ledger(tmp_path)
    called = []

    def counterfeit(_self):
        called.append("getter")
        return return_value

    with monkeypatch.context() as patch:
        patch.setattr(
            due.DueReservationWitness,
            "independent_custody_proven",
            property(counterfeit),
        )
        with pytest.raises(due.DueReservationRejected, match="witness authority"):
            _reserve(ledger, retained)
    assert called == []
    assert ledger.witness().count == 0


@pytest.mark.parametrize("return_value", (False, True))
def test_restart_rejects_counterfeit_custody_getter_before_execution(
    tmp_path, monkeypatch, return_value,
):
    ledger, retained = _ledger(tmp_path)
    called = []

    def counterfeit(_self):
        called.append("getter")
        return return_value

    with monkeypatch.context() as patch:
        patch.setattr(
            due.DueReservationWitness,
            "independent_custody_proven",
            property(counterfeit),
        )
        with pytest.raises(due.DueReservationRejected, match="witness authority"):
            due.DisconnectedDueReservations.reopen_with_witness(
                ledger._path, retained=retained,
            )
    assert called == []
    assert ledger.witness().count == 0


@pytest.mark.parametrize("return_value", (False, True))
def test_receipt_constructor_cannot_install_counterfeit_witness_before_commit(
    tmp_path, monkeypatch, return_value,
):
    ledger, retained = _ledger(tmp_path)
    original_init = due.DueReservationReceipt.__init__
    called = []

    def counterfeit(_self):
        called.append("getter")
        return return_value

    with monkeypatch.context() as patch:
        def altered_init(self, *args):
            original_init(self, *args)
            patch.setattr(
                due.DueReservationWitness,
                "independent_custody_proven",
                property(counterfeit),
            )

        patch.setattr(due.DueReservationReceipt, "__init__", altered_init)
        with pytest.raises(due.DueReservationRejected, match="constructor authority changed"):
            _reserve(ledger, retained)
    assert called == []
    # A preinstalled forged initializer is refused before a SQLite INSERT.
    # Other post-COMMIT uncertainties still prohibit blind replay.
    assert ledger.witness().count == 0


def test_witness_getter_cannot_rebind_its_class_on_last_access(
    tmp_path, monkeypatch,
):
    ledger, retained = _ledger(tmp_path)
    original_getattribute = due.DueReservationWitness.__getattribute__

    with monkeypatch.context() as patch:
        def altered_getattribute(self, name):
            value = original_getattribute(self, name)
            if name == "independent_custody_proven":
                patch.setattr(
                    due.DueReservationWitness, name,
                    property(lambda _self: False),
                )
            return value

        patch.setattr(
            due.DueReservationWitness, "__getattribute__",
            altered_getattribute,
        )
        with pytest.raises(due.DueReservationRejected, match="witness authority"):
            _reserve(ledger, retained)
    assert ledger.witness().count == 0


def test_witness_constructor_cannot_install_getter_before_first_review(
    monkeypatch,
):
    original_init = due.DueReservationWitness.__init__
    called = []

    def counterfeit(_self):
        called.append("getter")
        return False

    with monkeypatch.context() as patch:
        def altered_init(self, *args):
            original_init(self, *args)
            patch.setattr(
                due.DueReservationWitness,
                "independent_custody_proven",
                property(counterfeit),
            )

        patch.setattr(due.DueReservationWitness, "__init__", altered_init)
        with pytest.raises(due.DueReservationRejected, match="witness authority"):
            due.genesis_due_witness()
    assert called == []


def test_untouched_witness_is_restart_readable_and_inert(tmp_path):
    ledger, retained = _ledger(tmp_path)
    receipt = _reserve(ledger, retained)
    restarted = due.DisconnectedDueReservations.reopen_with_witness(
        ledger._path, retained=receipt.witness,
    )
    assert restarted.witness() == receipt.witness
    assert receipt.witness.independent_custody_proven is False
    assert receipt.execution_authorized is False
    assert receipt.notification_authorized is False
    assert receipt.automatic_replay_authorized is False
    assert receipt.trusted_clock_verified is False
