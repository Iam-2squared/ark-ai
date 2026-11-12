"""Private attention veto review rejects rebound output/digest callables.

Only disposable synthetic SQLite and hash-only fixture content is used.
A locally absent veto cannot establish consent, authority or a trusted clock.
"""

from __future__ import annotations

import pytest
from test_offline_attention_revocation_gate_run574 import _fixture, _review

import ark.offline_attention_revocation_review as join


@pytest.mark.parametrize("name", ("review_sha256", "__init__", "__getattribute__"))
def test_rebound_report_carrier_denied_before_private_ledger_read(
    tmp_path, monkeypatch, name,
):
    ledger, _, policy, retained = _fixture(tmp_path)
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(name)
        raise AssertionError("substituted output carrier should not execute")

    replacement = property(forbidden) if name == "review_sha256" else forbidden
    with monkeypatch.context() as patch:
        patch.setattr(join.AttentionRevocationReview, name, replacement)
        with pytest.raises(
            join.AttentionRevocationRejected,
            match="attention/veto report gained authority",
        ):
            _review(ledger, retained, policy)

    assert calls == []
    normal = _review(ledger, retained, policy)
    assert normal.attention_disposition == "REVIEW_ONLY"
    assert normal.notification_authorized is False
    assert normal.tool_execution_authorized is False


@pytest.mark.parametrize("name", ("sha256", "dumps"))
def test_rebound_digest_callback_denied_before_private_hashing(
    tmp_path, monkeypatch, name,
):
    ledger, _, policy, retained = _fixture(tmp_path)
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(name)
        raise AssertionError("rebound codec should not receive local evidence")

    module = join.hashlib if name == "sha256" else join.json
    with monkeypatch.context() as patch:
        patch.setattr(module, name, forbidden)
        with pytest.raises(
            join.AttentionRevocationRejected,
            match="original attention/veto authority changed",
        ):
            _review(ledger, retained, policy)

    assert calls == []
    normal = _review(ledger, retained, policy)
    assert normal.attention_disposition == "REVIEW_ONLY"
    assert normal.consent_verified is False
