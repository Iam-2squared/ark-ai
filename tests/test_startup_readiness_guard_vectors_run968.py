"""Run968: opt-in startup readiness guards retain complete trusted vectors.

Disconnected and mock-only. No device, local file, permission grant,
autonomous dispatch, or real application-data read occurs in this test.
"""

from __future__ import annotations

import pytest

from ark import disconnected_local_readiness as readiness


_VECTOR_NAMES = (
    "_STARTUP_GRANT_MEMBERS",
    "_SCHEMA_DENIALS",
    "_PREFLIGHT_DENIALS",
    "_REPORT_DENIALS",
    "_REPORT_FIELDS",
    "_REPORT_HOOKS",
    "_SCHEMA_CARRIER_NAMES",
    "_PREFLIGHT_CARRIER_NAMES",
)


@pytest.mark.parametrize("vector", _VECTOR_NAMES)
@pytest.mark.parametrize("replacement", ("empty", "equal-valued-clone"))
def test_guard_vector_rebinding_rejected_before_grant_read(
    monkeypatch, vector, replacement,
):
    called = []

    def poison(*_args, **_kwargs):
        called.append(True)
        raise AssertionError("unreviewed grant field must not be read")

    original = getattr(readiness, vector)
    replacement_value = (
        () if replacement == "empty" else tuple(list(original))
    )
    assert replacement_value is not original
    with monkeypatch.context() as patch:
        patch.setattr(readiness, vector, replacement_value)
        patch.setattr(readiness.CapabilityGrant, "scope", property(poison))
        with pytest.raises(
            readiness.DisconnectedLocalReadinessRejected,
            match="startup guard vector changed",
        ):
            readiness.review_disconnected_local_readiness(
                None, None, None, None, None, (), observed_at_ms=0,
            )
    assert called == []


def test_unmodified_startup_guards_keep_invalid_inputs_denied():
    readiness._require_original_denials()
    with pytest.raises(
        readiness.DisconnectedLocalReadinessRejected,
        match="invalid exact startup inputs",
    ):
        readiness.review_disconnected_local_readiness(
            None, None, None, None, None, (), observed_at_ms=0,
        )
