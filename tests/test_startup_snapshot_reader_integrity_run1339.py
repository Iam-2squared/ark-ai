"""Run1339: public startup snapshot readers pin integrity before dispatch.

All graph values are synthetic. No startup, dispatch, notification, device,
credential or live backend is activated.
"""

from __future__ import annotations

import ark.startup_readiness_review as readiness

import pytest


@pytest.mark.parametrize("reader_name", ("state", "root_blockers"))
def test_snapshot_reader_rejects_replaced_integrity_method_before_call(
    monkeypatch, reader_name: str,
) -> None:
    snapshot = readiness.evaluate_startup_readiness((
        readiness.StartupComponent("memory", schema_revision="v1"),
    ))
    calls: list[object] = []

    def substituted(self):
        calls.append(self)
        return None

    monkeypatch.setattr(
        readiness.StartupSnapshot,
        "_assert_integrity",
        substituted,
    )

    with pytest.raises(
        ValueError,
        match="startup constructor authority changed",
    ):
        getattr(snapshot, reader_name)("memory")

    assert calls == []
