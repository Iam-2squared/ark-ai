"""Strict UTF-8 byte-bound synthetic proactive policies, no notifications.

The policy is an inert local fixture. Invalid policy labels must be rejected
before any persisted trigger operation or privacy-bearing policy hash.
"""

from __future__ import annotations

import pytest

import ark.proactive_synthetic_review as proactive

_FIELDS = ("owner", "namespace", "definition_id", "policy_revision")


def _policy(field, value):
    data = {
        "owner": "fixture-owner",
        "namespace": "private",
        "definition_id": "scheduled-summary",
        "revision": 1,
        "policy_revision": "rev-1",
        "minimum_interval_ms": 1,
        "rolling_window_ms": 100,
        "max_preparations_per_window": 3,
    }
    data[field] = value
    return proactive.SyntheticTriggerPolicy(**data)


@pytest.mark.parametrize("field", _FIELDS)
@pytest.mark.parametrize(
    "invalid",
    ("é" * 257, "界" * 171, "\ud800", "a" * 513),
)
def test_proactive_policy_rejects_byte_overflow_or_surrogate_at_ingress(
    field, invalid,
):
    with pytest.raises(ValueError):
        _policy(field, invalid)


@pytest.mark.parametrize("field", _FIELDS)
@pytest.mark.parametrize("valid", ("é" * 256, "界" * 170))
def test_proactive_policy_accepts_valid_strict_utf8_boundary(field, valid):
    policy = _policy(field, valid)
    assert policy.identity()[_FIELDS.index(field) if field != "policy_revision" else 4] == (
        valid
    )


@pytest.mark.parametrize("invalid", ("é" * 257, "\ud800"))
def test_reflectively_changed_policy_is_rejected_before_sqlite_open(
    tmp_path, monkeypatch, invalid,
):
    ledger = proactive.SyntheticProactiveLedger(tmp_path / "proactive.sqlite")
    policy = _policy("owner", "valid-original")
    object.__setattr__(policy, "owner", invalid)

    def never_sqlite(*_args, **_kwargs):
        raise AssertionError("invalid synthetic policy reached sqlite.connect")

    with monkeypatch.context() as patch:
        patch.setattr(proactive.sqlite3, "connect", never_sqlite)
        with pytest.raises(ValueError):
            ledger.prepare(
                policy, source_digest="a" * 64, observation_digest="b" * 64,
                observed_at_ms=40, now_ms=50,
            )
