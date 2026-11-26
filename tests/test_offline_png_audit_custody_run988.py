"""Private synthetic PNG scanlines must not construct forged audit carriers."""

import hashlib
import zlib

import pytest

from ark import offline_png_scanlines as png


def _fixture():
    idat = zlib.compress(b"\x00\x11")
    return png.OfflineScanlineRequest(
        owner_sha256="a" * 64,
        privacy_sha256="b" * 64,
        idat_sha256=hashlib.sha256(idat).hexdigest(),
        idat_bytes=idat,
        width=1,
        height=1,
        color_type=0,
        bit_depth=8,
        palette_entries=0,
    )


def test_plain_local_scanline_still_has_denied_authority():
    request = _fixture()
    audit = png.inspect_offline_png_scanlines(request)
    assert audit.reconstructed_sha256 == hashlib.sha256(b"\x11").hexdigest()
    assert audit.filters_used == (1, 0, 0, 0, 0)
    png.verify_offline_png_scanlines(audit, request)
    for name in png._SCANLINE_DENIALS:
        assert getattr(audit, name) is False


@pytest.mark.parametrize("api", ["inspect", "verify"])
@pytest.mark.parametrize(
    "tamper",
    [
        "audit_init",
        "audit_slot",
        "audit_hook",
        "audit_denial",
        "audit_symbol",
        "paired_audit_vector",
        "paired_request_vector",
        "paired_denial_vector",
        "digest_helper",
        "paeth_helper",
    ],
)
def test_private_png_rejects_replaced_result_authority_before_codec(
    monkeypatch, api, tamper
):
    request = _fixture()
    original_audit = png.inspect_offline_png_scanlines(request)
    invoked = []

    def malicious(*args, **kwargs):
        invoked.append((args, kwargs))
        raise AssertionError("malicious fixture callback was reached")

    with monkeypatch.context() as m:
        if tamper == "audit_init":
            m.setattr(png.OfflineScanlineAudit, "__init__", malicious)
        elif tamper == "audit_slot":
            m.setattr(png.OfflineScanlineAudit, "filters_used", property(malicious))
        elif tamper == "audit_hook":
            m.setattr(png.OfflineScanlineAudit, "__getattribute__", malicious)
        elif tamper == "audit_denial":
            m.setattr(png.OfflineScanlineAudit, "user_consent_verified", property(malicious))
        elif tamper == "audit_symbol":
            m.setattr(png, "OfflineScanlineAudit", object)
        elif tamper == "paired_audit_vector":
            m.setattr(png, "_AUDIT_FIELDS", png._AUDIT_FIELDS[:-1])
            m.setattr(png, "_ORIGINAL_AUDIT_SLOTS", png._ORIGINAL_AUDIT_SLOTS[:-1])
        elif tamper == "paired_request_vector":
            m.setattr(png, "_REQUEST_FIELDS", png._REQUEST_FIELDS[:-1])
            m.setattr(png, "_ORIGINAL_REQUEST_SLOTS", png._ORIGINAL_REQUEST_SLOTS[:-1])
        elif tamper == "paired_denial_vector":
            m.setattr(png, "_SCANLINE_DENIALS", png._SCANLINE_DENIALS[:-1])
            m.setattr(
                png, "_SCANLINE_DENIAL_DESCRIPTORS",
                png._SCANLINE_DENIAL_DESCRIPTORS[:-1],
            )
        elif tamper == "digest_helper":
            m.setattr(png, "_sha", malicious)
        elif tamper == "paeth_helper":
            m.setattr(png, "_paeth", malicious)

        with pytest.raises(png.OfflineScanlineRejected):
            if api == "inspect":
                png.inspect_offline_png_scanlines(request)
            else:
                png.verify_offline_png_scanlines(original_audit, request)
    assert invoked == []
