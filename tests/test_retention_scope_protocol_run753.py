"""Retention inventory guards private scope carriers before any callback.

All data is synthetic local SQLite fixture state; no erasure, consent,
external access, billing, real clock or Tool dispatch is authorized.
"""

from __future__ import annotations

import pytest
from test_personal_context_retention_review_run376 import _review, _setup

import ark.personal_context_retention_review as retention
from ark.memory.contracts import MemoryScope


@pytest.mark.parametrize("member", (
    "owner_id", "namespace", "__init__", "__post_init__",
    "__getattribute__", "__getattr__",
))
def test_replaced_scope_carrier_refused_before_reading_private_scope(
    tmp_path, monkeypatch, member,
):
    state = _setup(tmp_path)
    invoked = []

    def forbidden(*_args, **_kwargs):
        invoked.append(member)
        raise AssertionError("private scope reached injected class callback")

    with monkeypatch.context() as patch:
        if member in ("owner_id", "namespace"):
            patch.setattr(MemoryScope, member, property(forbidden))
        else:
            patch.setattr(MemoryScope, member, forbidden, raising=False)
        with pytest.raises(
            retention.SyntheticRetentionRejected, match="dependency changed",
        ):
            _review(state)
    assert invoked == []
    report = _review(state)
    assert len(report.items) == 4
    assert report.erasure_completed is False
    assert report.deletion_authorized is False
    assert report.context_use_authorized is False


def test_retention_clock_limit_rebinding_does_not_expand_admission(
    tmp_path, monkeypatch,
):
    state = _setup(tmp_path)
    with monkeypatch.context() as patch:
        patch.setattr(retention, "_MAX", 2**80)
        with pytest.raises(
            retention.SyntheticRetentionRejected, match="dependency changed",
        ):
            _review(state, now_ms=2**70)
    assert _review(state).expired_count == 2
