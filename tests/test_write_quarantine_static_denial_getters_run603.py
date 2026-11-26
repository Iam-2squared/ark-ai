"""No counterfeit property getter runs during synthetic WRITE quarantine.

All evidence is caller-supplied; this fixture neither authorizes a real
action nor proves non-execution, consent, or cross-store atomicity.
"""

from __future__ import annotations

import pytest

import ark.agency.synthetic_write_quarantine_matrix_review as mod

_DENIALS = (
    (mod.SyntheticQuarantineFinding, "automatic_replay_authorized", "finding carrier"),
    (mod.SyntheticQuarantineMatrix, "dispatch_authorized", "result changed"),
    (mod.SyntheticQuarantineMatrix, "automatic_replay_authorized", "result changed"),
    (mod.SyntheticQuarantineMatrix, "external_outcome_known", "result changed"),
)


def _diagnose():
    row = mod.SyntheticWriteStoreObservation(
        "write_a", "pending", "absent", "absent", "absent",
    )
    return mod.diagnose_disconnected_write_quarantine(
        topology_digest="plan_" + "e" * 64,
        independently_expected_step_ids=("write_a",),
        observations=(row,),
    )


@pytest.mark.parametrize(("owner", "flag", "message"), _DENIALS)
@pytest.mark.parametrize("when", ("preinstalled", "hash_callback"))
def test_counterfeit_denial_getter_is_rejected_without_execution(
    monkeypatch, owner, flag, message, when,
):
    calls: list[int] = []

    class Counterfeit:
        def __get__(self, _instance, _owner=None):
            calls.append(1)
            return False

    counterfeit = Counterfeit()
    if when == "preinstalled":
        monkeypatch.setattr(owner, flag, counterfeit)
    else:
        original_hash = mod._hash

        def substitute_during_hash(data):
            monkeypatch.setattr(owner, flag, counterfeit)
            return original_hash(data)

        monkeypatch.setattr(mod, "_hash", substitute_during_hash)

    with pytest.raises(mod.SyntheticQuarantineMatrixRejected, match=message):
        _diagnose()
    assert calls == []


def test_unmodified_matrix_is_diagnostic_only():
    report = _diagnose()
    assert report.observed_write_step_ids == ("write_a",)
    assert report.findings[0].reasons == ("no_external_nonexecution_proof",)
    assert report.findings[0].automatic_replay_authorized is False
    assert report.dispatch_authorized is False
    assert report.automatic_replay_authorized is False
    assert report.external_outcome_known is False
