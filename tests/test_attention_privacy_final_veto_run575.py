"""A detached attention preview must not outrun a newly persisted veto.

Test-only synthetic ledger writes; no notification, device, consent or real
user data. The two reads still cannot provide a trusted atomic consent gate.
"""

from __future__ import annotations

import pytest
from test_offline_attention_revocation_gate_run574 import _fixture, _review

import ark.offline_attention_revocation_review as join
from ark.memory.contracts import MemoryScope


@pytest.mark.parametrize("same_scope", (True, False))
def test_inflight_revocation_change_invalidates_earlier_attention_review(
    tmp_path, monkeypatch, same_scope,
):
    ledger, owner_scope, policy, retained = _fixture(tmp_path)
    original_connect = ledger._connect
    readonly_reads = []

    def intercepted_connect(*, readonly):
        if readonly:
            readonly_reads.append(len(readonly_reads) + 1)
            if len(readonly_reads) == 2:
                scope = (
                    owner_scope if same_scope
                    else MemoryScope("synthetic-other", "foreign-namespace")
                )
                ledger.revoke(scope, at_ms=1400)
        return original_connect(readonly=readonly)

    monkeypatch.setattr(ledger, "_connect", intercepted_connect)
    with pytest.raises(
        join.AttentionRevocationRejected,
        match="local revocation changed during attention review",
    ):
        _review(ledger, retained, policy, now=1500)
    assert readonly_reads == [1, 2]


def test_unchanged_revocation_ledger_is_rechecked_before_review_only(
    tmp_path, monkeypatch,
):
    ledger, _, policy, retained = _fixture(tmp_path)
    original_connect = ledger._connect
    reads = []

    def counted_connect(*, readonly):
        if readonly:
            reads.append(True)
        return original_connect(readonly=readonly)

    monkeypatch.setattr(ledger, "_connect", counted_connect)
    report = _review(ledger, retained, policy)
    assert reads == [True, True]
    assert report.attention_disposition == "REVIEW_ONLY"
    assert report.notification_authorized is False
    assert report.consent_verified is False
