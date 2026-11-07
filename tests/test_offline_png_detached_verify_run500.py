"""Detached private PNG scanline integrity is not camera or action authority."""

import hashlib
import zlib
from dataclasses import replace

import pytest

from ark.offline_png_scanlines import (
    OfflineScanlineAudit,
    OfflineScanlineRejected,
    OfflineScanlineRequest,
    inspect_offline_png_scanlines,
    verify_offline_png_scanlines,
)


def example():
    payload = zlib.compress(b"\x00\x02\x05")
    request = OfflineScanlineRequest(
        "a" * 64, "b" * 64, hashlib.sha256(payload).hexdigest(),
        payload, 2, 1, 0, 8, 0,
    )
    return request, inspect_offline_png_scanlines(request)


def test_reverify_is_private_and_matches_exact_retained_bytes():
    request, audit = example()
    assert verify_offline_png_scanlines(audit, request) is None
    assert audit.reconstructed_sha256 == hashlib.sha256(b"\x02\x05").hexdigest()
    assert audit.filters_used == (1, 0, 0, 0, 0)
    assert not audit.capture_provenance_verified
    assert not audit.user_consent_verified
    assert not audit.observation_or_tool_authorized


@pytest.mark.parametrize("field,value", [
    ("idat_sha256", "f" * 64),
    ("reconstructed_sha256", "f" * 64),
    ("width", 3),
    ("height", True),
    ("inflated_bytes", 99),
    ("filters_used", (0, 1, 0, 0, 0)),
    ("filters_used", [1, 0, 0, 0, 0]),
    ("filters_used", (1, 0, 0, 0, -1)),
])
def test_detached_report_mutation_is_rejected(field, value):
    request, report = example()
    with pytest.raises(OfflineScanlineRejected):
        verify_offline_png_scanlines(replace(report, **{field: value}), request)


def test_independent_idat_custody_must_match():
    request, report = example()
    changed = zlib.compress(b"\x00\x03\x06")
    new_request = replace(
        request, idat_bytes=changed,
        idat_sha256=hashlib.sha256(changed).hexdigest(),
    )
    with pytest.raises(OfflineScanlineRejected, match="differs"):
        verify_offline_png_scanlines(report, new_request)


class FakeScanlineAudit(OfflineScanlineAudit):
    pass


def test_audit_subclass_cannot_provide_attestation():
    request, report = example()
    cloned = FakeScanlineAudit(
        report.idat_sha256, report.reconstructed_sha256, report.width,
        report.height, report.inflated_bytes, report.filters_used,
    )
    with pytest.raises(OfflineScanlineRejected):
        verify_offline_png_scanlines(cloned, request)


def test_reflected_audit_change_during_redecode_is_rejected(monkeypatch):
    import ark.offline_png_scanlines as module

    request, report = example()
    original = module.inspect_offline_png_scanlines

    def changed(req):
        object.__setattr__(report, "inflated_bytes", 999)
        return original(req)

    monkeypatch.setattr(module, "inspect_offline_png_scanlines", changed)
    with pytest.raises(OfflineScanlineRejected, match="changed"):
        verify_offline_png_scanlines(report, request)
