"""A synthetic privacy veto receipt must survive the final False getter.

All observations are disposable local fixtures, not consent or notification.
"""

from __future__ import annotations

import pytest
from test_offline_attention_revocation_gate_run574 import _fixture, _review

import ark.offline_attention_revocation_review as join


@pytest.mark.parametrize("field,value", (
    ("review_sha256", "f" * 64),
    ("attention_disposition", "FORGED"),
    ("revocation_count", 999),
))
def test_last_denial_getter_cannot_rewrite_detached_veto_receipt(
    tmp_path, monkeypatch, field, value,
):
    ledger, _, policy, retained = _fixture(tmp_path)
    report_type = join.AttentionRevocationReview
    original_getattribute = report_type.__getattribute__

    def changed(self, name):
        if name == "tool_execution_authorized":
            object.__setattr__(self, field, value)
            return False
        return original_getattribute(self, name)

    monkeypatch.setattr(report_type, "__getattribute__", changed)
    with pytest.raises(
        join.AttentionRevocationRejected,
        match="attention/veto report gained authority",
    ):
        _review(ledger, retained, policy)
    assert ledger.path.is_file()


def test_untouched_local_veto_report_is_still_non_authorizing(tmp_path):
    ledger, _, policy, retained = _fixture(tmp_path)
    result = _review(ledger, retained, policy)
    assert result.attention_disposition == "REVIEW_ONLY"
    assert result.vetoed is False
    assert result.notification_authorized is False
    assert result.tool_execution_authorized is False
